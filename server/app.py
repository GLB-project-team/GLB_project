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
    result, prompt = get_chat_response(user_question, client, collection_name)

    return jsonify({'response': result, 'prompt': prompt})

@app.route('/chromadb/peek', methods=['GET'])
def get_data_chromadb():
    from src.chroma_manager import chroma_init, get_chromadb_data
    collection_name = 'book_collection'
    client = chroma_init(collection_name)
    result = get_chromadb_data(client, collection_name)

    return jsonify({"response": result})

def get_chat_response(question, client, collection_name):
    from src.chroma_manager import chroma_search
    from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA

    similar_docs, search_db = chroma_search(client, collection_name, question)
    # max_similarity_doc = min(similar_docs, key=lambda x: x[1])[0].page_content
    print("similar_docs", flush=True)
    print(similar_docs, flush=True)
    if similar_docs:
        # context = "\n".join([doc.page_content for doc in similar_docs])
        context = "\n".join([doc[0].page_content for doc in similar_docs])
    else:
        context = '없음'
        similar_docs = []

    # 프롬프트 생성
    prompt = f"""You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.
    \nQuestion: {question}
    \nContext: {context}
    \nAnswer:"""
    print("컨텍스트다 이눔아", flush=True)
    print(context, flush=True)
    # LLM
    from langchain_openai import ChatOpenAI
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    # # RAG pipeline
    chain = (
        RunnablePassthrough(lambda x: prompt)  # 함수를 직접 전달
        | model
        | StrOutputParser()
    )

    # # 파이프라인 실행
    output = chain.invoke(question)
    # return output, template

    template="""
    You are an expert assistant for answering questions based on specific contextual information provided. Your task is to answer the question using only the provided context. If the answer is not clearly found within the context, state that you don't have enough information to answer. 

    The context provided includes important information about a book, such as the title, author, introduction, publisher review, and notable excerpts. 
    Here is the context:
    {context}

    Question: {question}

    Answer:
    """
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    retriever = search_db.as_retriever()

    qa_chain = RetrievalQA.from_chain_type(
        model,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain({"query": question})

    answer = result["result"]
    source_documents = result["source_documents"]

    print("Answer:", flush=True)
    print(answer, flush=True)
    print("\nContext:", flush=True)
    for doc in source_documents:
        print(doc.page_content, flush=True)

    return result["result"], template

@app.route('/crawler/request', methods=['POST'])
def request_craw_with_insert():
    from src.crawler import crawl_single_page
    from src.chroma_manager import chroma_init, db_insert, check_url_exists

    # POST 요청으로부터 URL 가져오기
    data = request.get_json()
    url = data.get('url')

    collection_name = 'book_collection'
    client = chroma_init(collection_name)

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if check_url_exists(client, collection_name, url):
        return jsonify({"message": f"Document with URL {url} already exists."}), 200
    else:
        doc = crawl_single_page(url)
        if doc:
            db_insert(client, collection_name, doc)
            return jsonify({"message": "Document inserted successfully"}), 201
        else:
            return jsonify({"error": "Failed to crawl the URL"}), 500

@app.route('/crawler/local', methods=['POST'])
def local_craw_with_insert():
    from src.crawler import crawling_manager

    doc = crawling_manager()
    return jsonify({"message": f"Document inserted successfully\n{doc}"}), 201

@app.route('/crawler/checkurl', methods=['GET'])
def check_url():
    from src.chroma_manager import check_url_exists, chroma_init

    url = "https://product.kyobobook.co.kr/detail/S000213800371"
    collection_name = 'book_collection'
    client = chroma_init(collection_name)

    doc = check_url_exists(client, collection_name, url)
    return jsonify({"message": f"Document inserted successfully\n{doc}"}), 201

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
