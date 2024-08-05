# Chroma 클라이언트 생성
# from langchain_community.embeddings import OpenAIEmbeddings
# from langchain.embeddings import OpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
import os
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def chroma_init(collection_name):
    client = chromadb.HttpClient(
        host="glb_project-chromadb-1", port=8000, settings=Settings(allow_reset=True)
    )
    # embeddings_function = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY, 
        model_name="text-embedding-ada-002"
    )
    # col = client.list_collections()
    # if not col[collection_name]:
    #     client.reset()  # 데이터베이스 초기화
    #     collection = client.create_collection(collection_name, embeddings_function=openai_ef)
    # else:
    #     collection = client.get_collention[collection_name]
    # collection = client.get_or_create_collention(
    #     collection_name, 
    #     embedding_function=openai_ef
    # )
    collections = client.list_collections()
    
    collection_names = [collection['name'] for collection in collections]

    if collection_name not in collection_names:
        client.reset()  # 데이터베이스 초기화
        collection = client.create_collection(collection_name, embeddings_function=openai_ef)
    else:
        collection = client.get_collection(collection_name)
    return client

def db_insert(client, collection_name, doc):
    # client = chromadb.HttpClient(
    #     host="glb_project-chromadb-1", port=8000, settings=Settings(allow_reset=True)
    # )
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY, 
        model_name="text-embedding-ada-002"
    )
    collection = client.get_collection(name=collection_name, embedding_function=openai_ef)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    # docs = text_splitter.split_text(documents)
    splits = text_splitter.split_text(doc.page_content)
    for i, split in enumerate(splits):
        from src.crawler import Document
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
    for doc in split_doc:
        uuid_val = uuid.uuid1()
        # print("Inserted documents for ", uuid_val)
        collection.add(ids=[str(uuid_val)], documents=doc.page_content)

def chroma_search(client, collection_name, query, k=5):
    # embeddings_function = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY, 
        model_name="text-embedding-ada-002"
    )

    # tell LangChain to use our client and collection name
    search_db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=openai_ef,
    )
    docs = search_db.similarity_search(query, k=k)
    # docs = search_db.similarity_search_with_score(query, k=k)
    return docs

def check_url_exists(client, collection_name, url):
    collection = client.get_collection(name=collection_name)
    # 메타데이터에서 URL 검색
    result = collection.get(where={"url": url})
    return bool(result['metadatas'])














#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=0
#     )

#     # Set up the embeddings model
#     embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
#     vectorstore = Chroma.from_chroma_db(
#         collection=collection,
#         embedding=embeddings_model
#     )

#     # Get top-k similar documents
#     # similar_docs = vectorstore.similarity_search(query=question, k=k)
#     embedding_vector = OpenAIEmbeddings().embed_query(query)
#     searched_docs = vectorstore.similarity_search_by_vector(embedding_vector, k=k)

#     search_db = Chroma(
#         client=client,
#         collection_name=collection,
#         embedding_function=embedding_function,
#     )
#     return searched_docs

# # # 문서를 로드하고 청크로 분할합니다.
# # loader = TextLoader("./data/appendix-keywords.txt")
# # text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
# # docs = loader.load_and_split(text_splitter)

# # for i, doc in enumerate(docs):
# #     doc.metadata["chunk_id"] = i  # Chunk ID 추가
# #     # 무작위로 임의의 페이지 번호를 삽입합니다.
# #     doc.metadata["page_number"] = random.randint(0, 5)
# #     collection.add(
# #         ids=[str(uuid.uuid1())],
# #         metadatas=doc.metadata,
# #         documents=doc.page_content,
# #     )

# # # LangChain에게 클라이언트와 컬렉션 이름 사용 지시
# # db4 = Chroma(
# #     client=client,
# #     collection_name="chroma_docker",
# #     embedding_function=stf_embeddings,
# # )
# # query = "What is Word2Vec?"
# # docs = db4.similarity_search(query)
# # print(docs[0].page_content)
