# Chroma 클라이언트 생성
# from langchain.embeddings import OpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
import os
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def get_chromadb_data(client, collection_name):
    collection = client.get_collection(collection_name)
    #return collection.peek()
    all_docs = collection.get()  # 모든 데이터 들어갔는지 확인
    return all_docs

def chroma_init(collection_name):
    client = chromadb.HttpClient(
        host="glb_project-chromadb-1", port=8000, settings=Settings(allow_reset=True)
    )
    # collections = client.list_collections()
    # collection_names = [collection.name for collection in collections]

    try:
        collection = client.get_collection(collection_name)
        print('get collection')
    except:
        #client.reset()  # 데이터베이스 초기화
        collection = client.create_collection(collection_name)
        print('create collection')
    return client

def db_insert(client, collection_name, doc):
    print('start chromadb_insert')
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
    split_docs = []  # split_doc 객체를 저장할 리스트
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
        split_docs.append(split_doc)

    for split_doc in split_docs:
        uuid_val = uuid.uuid1()
        collection.add(ids=[str(uuid_val)], documents=split_doc.page_content, metadatas=split_doc.metadata)
        # collection.add(ids=[str(uuid_val)], documents=split_doc.page_content)

def chroma_search(client, collection_name, query, metadata_field=None, k=5):
    openai_ef = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # tell LangChain to use our client and collection name
    search_db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=openai_ef,
    )


    # if metadata_field:
    #     # 메타데이터 필터링이 필요한 경우, 직접 메타데이터를 필터링
    #     # 우선 검색 후, 메타데이터 기반으로 결과를 필터링
    #     docs = search_db.similarity_search_with_score(query, k=k)
    #     filtered_docs = [doc for doc in docs if metadata_field in doc[0].metadata]
    # else:
    #     filtered_docs = search_db.similarity_search_with_score(query, k=k)
    # return filtered_docs

    if metadata_field:
        docs = search_db.similarity_search_with_score(f"{metadata_field}: {query}", k=1)
    else:
        docs = search_db.similarity_search_with_score(query, k=1)
    return docs

    # docs = search_db.similarity_search(query, k=k)
    # docs = search_db.similarity_search_with_score(query)
    #return docs

def check_url_exists(client, collection_name, url):
    try:
        collection = client.get_collection(collection_name)
    except:
        return False

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
