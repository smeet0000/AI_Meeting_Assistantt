import os
import shutil
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

CHROMA_DIR = 'vector_db'
COLLECTION_NAME = 'meeting_transcripts'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {'device' : 'cpu'}
    )

def build_vector_store(transcript : str) -> Chroma:
    print('Building vector Store')

    Splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )
    chunks = Splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk,metadata={'chunk_index':i})
        for i,chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()

    # Delete the previous vector store
    if os.path.exists(CHROMA_DIR):
        print("Deleting old vector store...")

        try:
            old_store = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=embeddings,
                persist_directory=CHROMA_DIR
            )

            old_store.delete_collection()

        except Exception as e:
            print("Delete collection error:", e)

        shutil.rmtree(CHROMA_DIR, ignore_errors=True)


    vector_store = Chroma.from_documents(
        documents = docs,
        embedding= embeddings,
        collection_name= COLLECTION_NAME,
        persist_directory= CHROMA_DIR
    )

    return vector_store

def load_vector_store() -> Chroma:
    embedding = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function= embedding,
        persist_directory=CHROMA_DIR
    )

    return vector_store

def get_retriver(transcript:str,vector_store: Chroma,k :int = 4):
    # # return vector_store.as_retriever(
    # #     search_type = 'similarity',
    # #     search_kwargs = {'k':k}
    # )
    dense_retriver = vector_store.as_retriever(
        search_type = 'similarity',
        search_kwargs = {'k':k},
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50,
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk,metadata = {'chunk_id':i},)
        for i,chunk in enumerate(chunks)
    ]

    bm25_retriver = BM25Retriever.from_documents(docs)
    bm25_retriver.k = k

    hybrid_retriver = EnsembleRetriever(
        retrievers=[
            dense_retriver,
            bm25_retriver,
        ],
        weights=[
            0.7,
            0.3,
        ],
    )

    return hybrid_retriver