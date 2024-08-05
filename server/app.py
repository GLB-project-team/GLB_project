# app.py
from flask import Flask, request, render_template, jsonify

# Flask 애플리케이션 초기화
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_question = data.get('question', '')
    if user_question.lower() in ['exit', 'quit', 'q']:
        return jsonify({'response': 'Goodbye!'})
    from src.chroma_manager import chroma_init
    collection_name = "book_collection"
    client = chroma_init(collection_name)
    result = get_chat_response(user_question, client, collection_name)

    return jsonify({'response': result})

@app.route('/chromadb/peek', methods=['GET'])
def get_data_chromadb():
    from src.chroma_manager import chroma_init, get_chromadb_data
    collection_name = 'book_collection'
    client = chroma_init(collection_name)
    print(get_chromadb_data(client, collection_name))
    return jsonify({"message": "Document inserted successfully"}), 201

def get_chat_response(question, client, collection_name):
    from src.chroma_manager import chroma_search
    similar_docs = chroma_search(client, collection_name, question)
    # max_similarity_doc = min(similar_docs, key=lambda x: x[1])[0].page_content
    print(similar_docs)
    if similar_docs:
        # context = "\n".join([doc.page_content for doc in similar_docs])
        context = "\n".join([doc[0].page_content for doc in similar_docs])
    else:
        context = '없음'
        similar_docs = []
    # print('ㅅㅇㅅㅇㄴㅁ')
    # print(context)
    # 프롬프트 생성
    prompt = f"""You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.
    \nQuestion: {question}
    \nContext: {context}
    \nAnswer:"""

    # LLM
    from langchain_openai import ChatOpenAI
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    # RAG pipeline
    chain = (
        RunnablePassthrough(lambda x: prompt)  # 함수를 직접 전달
        | model
        | StrOutputParser()
    )

    # 파이프라인 실행
    output = chain.invoke(question)
    return output

@app.route('/crawler/request', methods=['POST'])
def request_craw_with_insert():
    from src.crawler import crawl_single_page
    from src.chroma_manager import chroma_init, db_insert, check_url_exists
    url = 0
    collection_name = 'book_collection'
    client = chroma_init(collection_name)

    if check_url_exists(client, collection_name, url):
        print(f"Document with URL {url} already exists.")
    else:
        doc = crawl_single_page(url)
        if doc:
            db_insert(client, collection_name, doc)
    return jsonify({"message": "Document inserted successfully"}), 201

@app.route('/crawler/local', methods=['POST'])
def local_craw_with_insert():
    from src.crawler import crawling_manager

    doc = crawling_manager()
    return jsonify({"message": f"Document inserted successfully\n{doc}"}), 201

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
