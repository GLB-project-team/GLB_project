# Chroma 클라이언트 생성
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
import os
import uuid
import random
import chromadb

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def chroma_init(collection_name):
    client = chromadb.HttpClient(
        host="0.0.0.0", port=8000, settings=Settings(allow_reset=True)
    )
    # col = client.list_collections()
    # if not col[collection_name]:
    #     client.reset()  # 데이터베이스 초기화
    #     collection = client.create_collection(collection_name)
    # else:
    #     collection = client.get_collention[collection_name]
    embeddings_function = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    collection = client.get_or_create_collention(
        collection_name, 
        embedding_function=embeddings_function
    )
    return client

def chroma_search(client, collection_name, query, k=5):
    embeddings_function = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # tell LangChain to use our client and collection name
    search_db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings_function,
    )
    docs = search_db.similarity_search(query, k=k)
    return docs

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )

    # Set up the embeddings model
    embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = Chroma.from_chroma_db(
        collection=collection,
        embedding=embeddings_model
    )

    # Get top-k similar documents
    # similar_docs = vectorstore.similarity_search(query=question, k=k)
    embedding_vector = OpenAIEmbeddings().embed_query(query)
    searched_docs = vectorstore.similarity_search_by_vector(embedding_vector, k=k)

    search_db = Chroma(
        client=client,
        collection_name=collection,
        embedding_function=embedding_function,
    )
    return searched_docs

# # 문서를 로드하고 청크로 분할합니다.
# loader = TextLoader("./data/appendix-keywords.txt")
# text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
# docs = loader.load_and_split(text_splitter)

# for i, doc in enumerate(docs):
#     doc.metadata["chunk_id"] = i  # Chunk ID 추가
#     # 무작위로 임의의 페이지 번호를 삽입합니다.
#     doc.metadata["page_number"] = random.randint(0, 5)
#     collection.add(
#         ids=[str(uuid.uuid1())],
#         metadatas=doc.metadata,
#         documents=doc.page_content,
#     )

# # LangChain에게 클라이언트와 컬렉션 이름 사용 지시
# db4 = Chroma(
#     client=client,
#     collection_name="chroma_docker",
#     embedding_function=stf_embeddings,
# )
# query = "What is Word2Vec?"
# docs = db4.similarity_search(query)
# print(docs[0].page_content)
