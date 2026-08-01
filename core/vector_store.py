import os
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = 'vector_db'
COLLECTION_NAME = 'meeting_transcripts'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

def get_embeddings():
    return HuggingFaceBgeEmbeddings(
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
        collection_name=CHROMA_DIR,
        embedding_function= embedding,
        persist_directory=CHROMA_DIR
    )

    return vector_store

def get_retriver(vector_store: Chroma,k :int = 4):
    return vector_store.as_retriever(
        search_type = 'similarity',
        search_kwargs = {'k':k}
    )
