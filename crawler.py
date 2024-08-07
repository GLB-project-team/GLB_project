import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class CustomDocument:
    def __init__(self, page_content, metadata):
        self.id = str(uuid.uuid4())
        self.page_content = page_content
        self.metadata = metadata

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

def crawl_book_data(urls):
    documents = []
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    try:
        for url in urls:
            driver.get(url)
            print(f"Successfully retrieved the web page: {url}")

            title = extract_element(wait, '//*[@id="contents"]/div[1]/div/div[1]/div/div[1]/div[1]/div/h1/span', "Title")
            author = extract_element(wait, '//*[@id="contents"]/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div[1]/div/div', "Author")
            toc = extract_elements(wait, '//*[@id="scrollSpyProdInfo"]/div[10]/div[2]/div[1]/div/ul/li', "Table of contents")
            book_intro = extract_elements(wait, '//*[@id="scrollSpyProdInfo"]/div[11]/div[2]/div[1]/div/p', "Book intro")
            publisher_review = extract_elements(wait, '//*[@id="scrollSpyProdInfo"]/div[12]/div[2]/div[1]/div/p', "Publisher review")
            review_str = extract_reviews(wait)

            page_content = f"제목:{title}\n\n작가 이름: {author}\n\n목차: {toc}\n\n책 속으로: {book_intro}\n\n출판사 서평: {publisher_review}\n\n리뷰: {review_str}"
            
            doc = CustomDocument(
                page_content=page_content,
                metadata={
                    'title': title,
                    'author': author,
                    'table_of_contents': toc,
                    'book_intro': book_intro,
                    'publisher_review': publisher_review,
                    'review': review_str,
                    'url': url
                }
            )
            documents.append(doc)

    finally:
        driver.quit()

    return documents

def extract_element(wait, xpath, element_name):
    try:
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return element.text.strip()
    except Exception as e:
        print(f"{element_name} not found: {e}")
        return "N/A"

def extract_elements(wait, xpath, element_name):
    try:
        elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        return "\n".join([item.text.strip() for item in elements])
    except Exception as e:
        print(f"{element_name} not found: {e}")
        return "N/A"

def extract_reviews(wait):
    try:
        review_selector = (
            'div.comment_list > div.comment_item > div.comment_contents '
            '> div.comment_contents_inner > div.comment_view_wrap '
            '> div.comment_text_box > div.comment_text'
        )
        review_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, review_selector)))
        return "\n".join([item.text.strip() for item in review_elements])
    except Exception as e:
        print(f"Reviews not found: {e}")
        return "N/A"

def process_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )

    all_splits = []
    for doc in documents:
        splits = text_splitter.split_text(doc.page_content)
        for i, split in enumerate(splits):
            split_doc = Document(
                page_content=split,
                metadata={
                    'id': f"{doc.id}-{i}",
                    'author': doc.metadata['author'],
                    'title': doc.metadata['title'],
                    'url': doc.metadata['url'],
                    'table_of_contents': doc.metadata['table_of_contents'],
                    'book_intro': doc.metadata['book_intro'],
                    'publisher_review': doc.metadata['publisher_review'],
                    'review': doc.metadata['review']
                }
            )
            all_splits.append(split_doc)

    return all_splits

def crawl_and_process(urls):
    documents = crawl_book_data(urls)
    return process
