# app.py
from flask import Flask, request, render_template, jsonify
from src.chroma_manager import chroma_search

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
    data = get_chromadb_data(client, collection_name)
    print(data)  
    #print(get_chromadb_data(client, collection_name))
    return jsonify({"message": "Document inserted successfully", "data":data}), 201

def get_chat_response(question, client, collection_name):

    # 특정 메타데이터를 참조하도록 질문 분석
    metadata_field = None
    if '목차' in question:
        metadata_field = 'table_of_contents'
    elif '출판사 서평' in question:
        metadata_field = 'publisher_review'
    # 더 많은 필드 추가 가능

    # 메타데이터 검색
    if metadata_field:
        similar_docs = chroma_search(client, collection_name, question, metadata_field)
        #print(f"similar_docs: {similar_docs}")
        #print(f"metadata_field: {metadata_field}")
    else:
        similar_docs = chroma_search(client, collection_name, question)
    #print(f"similar_docs: {similar_docs}")

    #질문에 해당 단어가 포함된 책 찾기
    if similar_docs:
        book_details = []
        for doc in similar_docs:
            metadata = doc[0].metadata
            # 문서의 메타데이터와 페이지 내용을 포함
            metadata_str = "\n".join([f"{key}: {value}" for key, value in metadata.items()])
            page_content = doc[0].page_content
            book_info = f"Metadata:\n{metadata_str}\nContent:\n{page_content}"
            book_details.append(book_info)
        context = "\n\n".join(book_details)
    # elif similar_docs:
    #     context = "\n".join([doc[0].page_content for doc in similar_docs])
    #     for doc in similar_docs: 
    #         print(f"similar_docs있으면 : {doc}")
    else:
        context = '없음'

    print("------------------context------------------\n", context)

# def get_chat_response(question, client, collection_name):
#     from src.chroma_manager import chroma_search
#     similar_docs = chroma_search(client, collection_name, question)
#     # max_similarity_doc = min(similar_docs, key=lambda x: x[1])[0].page_content
#     print(similar_docs)
#     if similar_docs:
#         # context = "\n".join([doc.page_content for doc in similar_docs])
#         context = "\n".join([doc[0].page_content for doc in similar_docs])
#     else:
#         context = '없음'
#         similar_docs = []
    # print('ㅅㅇㅅㅇㄴㅁ')
    # print(context)
    # 프롬프트 생성
    # prompt = f"""You are an assistant for question-answering tasks.
    # Use the following pieces of retrieved context to answer the question.
    # If you don't know the answer, just say that you don't know.
    # Use three sentences maximum and keep the answer concise.
    # \nQuestion: {question}
    # \nContext: {context}
    # \nAnswer:"""
    # prompt = f"""
    # You are an expert assistant for answering questions based on specific contextual information provided. Your task is to answer the question using only the provided context. If the answer is not clearly found within the context, state that you don't have enough information to answer. 

    # The context provided includes important information about a book, such as the title, author, introduction, publisher review, and notable excerpts. 
    # Here is the context:
    # {context}

    # Question: {question}

    # Answer:
    # """

    # LLM
    from langchain_openai import ChatOpenAI
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain.chains import RetrievalQA
    from langchain.vectorstores import Chroma
    from langchain.prompts import PromptTemplate
    from langchain.embeddings import OpenAIEmbeddings

    prompt = PromptTemplate(
        template="""
        You are an expert assistant for answering questions based on specific contextual information provided. Your task is to answer the question using only the provided context. If the answer is not clearly found within the context, state that you don't have enough information to answer. 

        The context provided includes important information about a book, such as the title, author, introduction, publisher review, and notable excerpts. 
        Here is the context:
        {context}

        Question: {question}

        Answer:
        """,
        input_variables=["context", "question"]
    )
    

    model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    # # RAG pipeline
    # chain = (
    #     RunnablePassthrough(lambda x: prompt)  # 함수를 직접 전달
    #     | model
    #     | StrOutputParser()
    # )
    # output = qa_chain.invoke(question)
    #return output


    # Define the embedding function
    embedding_function = OpenAIEmbeddings()

    # Initialize Chroma vector store with embedding function
    vectorstore = Chroma(client=client, collection_name=collection_name, embedding_function=embedding_function)
    
    qa_chain = RetrievalQA.from_chain_type(
    llm=model,
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": prompt}
)

    output = qa_chain({"query": question})
    return output['result']


    # vectorstore = Chroma(client=client, collection_name=collection_name)
    # #retriever = vectorstore.as_retriever()

    # qa_chain = RetrievalQA.from_chain_type(
    #     llm=model,
    #     retriever=vectorstore.as_retriever(),
    #     chain_type_kwargs={"prompt": prompt}
    # )

    # output = qa_chain(question)
    # return output

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
