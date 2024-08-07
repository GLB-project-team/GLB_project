# app.py
from flask import Flask, request, render_template, jsonify
from langchain.memory import ConversationBufferMemory
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

def get_chat_response(question, client, collection_name, chat_history = None):
    from src.chroma_manager import chroma_search
    from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA
    from langchain_openai import ChatOpenAI
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    # ChromaDB 검색 실행
    similar_docs, search_db = chroma_search(client, collection_name, question)
    if not similar_docs:
        # ChromaDB에서 문서를 찾지 못했을 경우, GPT 모델을 이용해 직접 답변 생성
        prompt = """You are an assistant for question-answering tasks.
            Use your knowledge to answer the question.
            If you don't know the answer, just say that you don't know.
            Use three sentences maximum and keep the answer concise.
            Here is the context:{context}
            \nQuestion: {question}
            \nAnswer:"""
        model = ChatOpenAI(temperature=2, model="gpt-3.5-turbo")
        chain = (
            RunnablePassthrough(lambda x: prompt)  # 프롬프트 직접 전달
            | model
            | StrOutputParser()
        )
        output = chain.invoke(question)
        return output, prompt

    # 문서가 존재할 경우, 검색된 문서를 사용하여 답변 생성
    template = """
    너는 책 추천 assistant야. context를 기반으로 question에 대한 대답을 다음과 같은 형식으로 대답해줘. 각 항목은 다른 문단으로 작성해줘.
    첫 문장은 예시와 같이 현재 상황을 공감하는 말을 해줘. (예시. user : 동물이 나오는 줄거리의 책을 추천해줘. ai : 동물이 나오는 줄거리의 책을 원하시는군요!)
    
    
    ♥책 제목:
    ♥목차 : \n
    ♥저자 : \n
    ♥책 내용 요약: \n
    ♥책 리뷰 요약: \n
    ♥책 추천 이유: \n
            \n{chat_history}
            \nContext:{context}
            \nQuestion: {question}
            \nAnswer:
    """
    
    if chat_history:
        chat_history_text = "\n이전 대화 내용 요약:" + chat_history
    else:
        chat_history_text=""


    prompt_template = PromptTemplate(
        template=template,
        input_variables=["context", "question", "chat_history"]
    )
    retriever = search_db.as_retriever()
    model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    qa_chain = RetrievalQA.from_chain_type(
        model,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template,
                           "memory": ConversationBufferMemory(memory_key="chat_history", input_key="question")}
    )
    inputs = {
        "query": question,
        "chat_history": chat_history_text  # 'chat_history' 키를 포함하여 입력값 설정
    }

    result = qa_chain(inputs)
    answer = result["result"]
    source_documents = result["source_documents"]

    context = "\n".join([doc.page_content for doc in source_documents])
    return answer, context


# def get_chat_response(question, client, collection_name):
#     from src.chroma_manager import chroma_search
#     from langchain.prompts import PromptTemplate
#     from langchain.chains import RetrievalQA
#     from langchain_openai import ChatOpenAI
#     from langchain_core.output_parsers import StrOutputParser

#     # ChromaDB 검색 실행
#     similar_docs, search_db = chroma_search(client, collection_name, question)
#     if not similar_docs:
#         # ChromaDB에서 문서를 찾지 못했을 경우, GPT 모델을 이용해 직접 답변 생성
#         model = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")
#         prompt = f"Here is a question that needs your expertise: {question}\n\nCan you provide a thoughtful and informative response based on what you know?"
#         response = model.generate(prompt, max_tokens=150)
#         return response["choices"][0]["text"], "GPT-3.5 Model Response"

#     # 문서가 존재할 경우, 검색된 문서를 사용하여 답변 생성
#     context = "\n".join([doc[0].page_content for doc in similar_docs]) if similar_docs else "No relevant information available."
#     prompt = f"""
#     You are an expert assistant for answering questions based on specific contextual information provided. Your task is to answer the question using only the provided context. If the answer is not clearly found within the context, state that you don't have enough information to answer. 

#     Context:
#     {context}

#     Question: {question}

#     Answer:
#     """
#     model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
#     response = model.generate(prompt, max_tokens=150)
#     return response["choices"][0]["text"], "Provided Context from ChromaDB"


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

# def get_chat_response(question, client, collection_name):
#     from src.chroma_manager import chroma_search
#     from langchain.prompts import PromptTemplate
#     from langchain.chains import RetrievalQA
#     from langchain_openai import ChatOpenAI
#     from langchain_core.output_parsers import StrOutputParser

#     # ChromaDB 검색 실행
#     similar_docs, search_db = chroma_search(client, collection_name, question)
#     if not similar_docs:
#         # ChromaDB에서 문서를 찾지 못했을 경우, GPT 모델을 이용해 직접 답변 생성
#         model = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")
#         prompt = f"Here is a question that needs your expertise: {question}\n\nCan you provide a thoughtful and informative response based on what you know?"
#         response = model.generate(prompt, max_tokens=150)
#         return response["choices"][0]["text"], "GPT-3.5 Model Response"

#     # 문서가 존재할 경우, 검색된 문서를 사용하여 답변 생성
#     context = "\n".join([doc[0].page_content for doc in similar_docs]) if similar_docs else "No relevant information available."
#     prompt = f"""
#     You are an expert assistant for answering questions based on specific contextual information provided. Your task is to answer the question using only the provided context. If the answer is not clearly found within the context, state that you don't have enough information to answer. 

#     Context:
#     {context}

#     Question: {question}

#     Answer:
#     """
#     model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
#     response = model.generate(prompt, max_tokens=150)
#     return response["choices"][0]["text"], "Provided Context from ChromaDB"


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