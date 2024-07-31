# app.py
from flask import Flask, request, render_template, jsonify

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain.chains import RetrievalQA
import os
import uuid
import time

# Flask 애플리케이션 초기화
app = Flask(__name__)

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

documents = []
# 웹 드라이버 초기화
# driver = webdriver.Chrome(options=chrome_options)
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

urls = [
    'https://product.kyobobook.co.kr/detail/S000213800371',      # 당신이 누군가를 죽였다.
    'https://product.kyobobook.co.kr/detail/S000213567877',      # 동경
    'https://product.kyobobook.co.kr/detail/S000213682152',      # 온전히 평등하고 지극히 차별적인
    'https://product.kyobobook.co.kr/detail/S000213900198',      # 쌤쌤 쿡북
    'https://product.kyobobook.co.kr/detail/S000213848131',      # 저속노화 식사법
    'https://product.kyobobook.co.kr/detail/S000213133026',      # 하나님, 그래서 그러셨군요!
    'https://product.kyobobook.co.kr/detail/S000213740560',      # 전지적 루이 & 후이 시점
    'https://product.kyobobook.co.kr/detail/S000213368065',      # THE MONEY BOOK(더 머니북)
    'https://product.kyobobook.co.kr/detail/S000213495686',      # 나만의 GPTs 앱으로 생산성 10배 늘리기
    'https://product.kyobobook.co.kr/detail/S000212058462',      # 디스 이즈 도쿄(2024~2025)
    'https://product.kyobobook.co.kr/detail/S000213513428',      # 부모의 어휘력
    'https://product.kyobobook.co.kr/detail/S000213641159',      # 마녀와의 7일
    'https://product.kyobobook.co.kr/detail/S000213641247',      # 탕비실
    'https://product.kyobobook.co.kr/detail/S000213835380',      # 역사의 쓸모
    'https://product.kyobobook.co.kr/detail/S000213690458',      # 무서운 그림들
    'https://product.kyobobook.co.kr/detail/S000213674078',      # 디자이너의 유학
    'https://product.kyobobook.co.kr/detail/S000213719520',      # 출근길 지하철
]

# 페이지 로드
wait = WebDriverWait(driver, 10)

try:
    for url in urls:
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
        documents.append(doc)

finally:
    # 드라이버 종료
    driver.quit()

# 문서 분할 및 벡터 저장소 생성
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

# os.environ["OPENAI_API_KEY"] = openai_key
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

vectorstore = Chroma.from_documents(
    documents=all_splits,
    embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
)

prompt = ChatPromptTemplate(input_variables=['context', 'question'],
                            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                                input_variables=['context', 'question'],
                                template=
                                '''You are an assistant for question-answering tasks.
                                Use the following pieces of retrieved context to answer the question.
                                If you don't know the answer, just say that you don't know.
                                Use three sentences maximum and keep the answer concise.
                                \nQuestion: {question}
                                \nContext: {context}
                                \nAnswer:'''
                            ))])

model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

qa_chain = RetrievalQA.from_chain_type(
    llm=model,
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": prompt}
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.form['question']
    if user_question.lower() in ['exit', 'quit', 'q']:
        return jsonify({'response': 'Goodbye!'})
    result = get_chat_response(user_question)
    return jsonify({'response': result})

def get_chat_response(question):
    response = qa_chain({"query": question})
    return response["result"]

if __name__ == "__main__":
    app.run(debug=True)
