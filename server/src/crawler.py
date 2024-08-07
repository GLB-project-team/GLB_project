from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import sqlite3
import hashlib
import uuid
import os


# Document 클래스 정의
class Document:
    def __init__(self, page_content, metadata):
        self.id = str(uuid.uuid4())
        self.page_content = page_content
        self.metadata = metadata

# Chrome 옵션 설정 (헤드리스 모드로 실행)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# def url_to_hash(url):
#     return hashlib.sha256(url.encode()).hexdigest()

# def is_url_crawled(url):
#     url_hash = url_to_hash(url)
#     c.execute('SELECT 1 FROM crawled_urls WHERE url_hash=?', (url_hash,))
#     return c.fetchone() is not None

def get_urls_in_csv(file_path='src/crawling_urls.csv'):
    try:
        df = pd.read_csv(file_path, names=['url', 'book_name'], dtype=str, header=0, quotechar='"', on_bad_lines='skip')
        urls = df['url'].tolist()  # 첫 번째 열만 추출
        return urls
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV: {e}")
        return []

def crawling_manager():
    from src.chroma_manager import chroma_init, db_insert, check_url_exists
    print('start crawling manager')
    urls = get_urls_in_csv()
    if not urls:
        return {"message": "No valid URLs found in CSV"}
    collection_name = 'book_collection'

    client = chroma_init(collection_name)
    for url in urls:
        print(url)
        if check_url_exists(client, collection_name, url):
            print(f"Document with URL {url} already exists.")
            continue  # 중복된 경우 크롤링을 건너뜁니다.

        # 중복되지 않은 경우에만 크롤링 진행
        document = crawl_single_page(url)
        if document:
            db_insert(client, collection_name, document)
    return urls

def crawl_single_page(url):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)
        print(f"Successfully retrieved the web page: {url}")

        # 제목 추출
        try:
            title_xpath = '//*[@id="contents"]/div[1]/div/div[1]/div/div[1]/div[1]/div/h1/span'
            title_element = wait.until(EC.presence_of_element_located((By.XPATH, title_xpath)))
            title = title_element.text
        except Exception as e:
            title = "N/A"
            print(f"Title not found for {url}: {e}")

        # 작가 이름 추출
        try:
            author_xpath = '//*[@id="contents"]/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div[1]/div/div'
            author_element = wait.until(EC.presence_of_element_located((By.XPATH, author_xpath)))
            author = author_element.text.strip()
        except Exception as e:
            author = "N/A"
            print(f"Author not found for {url}: {e}")

        # 목차 추출
        try:
            toc_xpath = '//*[@id="scrollSpyProdInfo"]/div[10]/div[2]/div[1]/div/ul/li'
            toc_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, toc_xpath)))
            toc_content = [item.text.strip() for item in toc_elements]
            toc = "\n".join(toc_content)
        except Exception as e:
            toc = "N/A"
            print(f"Table of contents not found for {url}: {e}")

        # 책 속으로 추출
        try:
            book_intro_xpath = '//*[@id="scrollSpyProdInfo"]/div[11]/div[2]/div[1]/div/p'
            book_intro_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, book_intro_xpath)))
            book_intro_content = [item.text.strip() for item in book_intro_elements]
            book_intro = "\n".join(book_intro_content)
        except Exception as e:
            book_intro = "N/A"
            print(f"Book intro not found for {url}: {e}")

        # 출판사 서평 추출
        try:
            publisher_review_xpath = '//*[@id="scrollSpyProdInfo"]/div[12]/div[2]/div[1]/div/p'
            publisher_review_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, publisher_review_xpath)))
            publisher_review_content = [item.text.strip() for item in publisher_review_elements]
            publisher_review = "\n".join(publisher_review_content)
        except Exception as e:
            publisher_review = "N/A"
            print(f"Publisher review not found for {url}: {e}")

        # 리뷰 추출
        try:
            review_selector = (
                'div.comment_list > div.comment_item > div.comment_contents '
                '> div.comment_contents_inner > div.comment_view_wrap '
                '> div.comment_text_box > div.comment_text'
            )
            review_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, review_selector)))
            review_content = [item.text.strip() for item in review_elements]
            review_str = "\n".join(review_content)
        except Exception as e:
            review_str = "N/A"
            print(f"Reviews not found for {url}: {e}")

        page_content = f"제목:{title}\n\n작가 이름: {author}\n\n목차: {toc}\n\n책 속으로: {book_intro}\n\n출판사 서평: {publisher_review}\n\n리뷰: {review_str}"
        # Document 객체 생성 및 추가
        doc = Document(
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
        return doc
    except:
        print('crawling error!')
        return None
    finally:
        # 드라이버 종료
        driver.quit()
