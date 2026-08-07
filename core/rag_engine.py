import os
from langchain_mistralai import ChatMistralAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda,RunnablePassthrough
from core.vector_store import build_vector_store,load_vector_store,get_retriver
from core.reranker import rerank_documents

def get_llm():
    return ChatMistralAI(model = "mistral-small-latest",mistral_api_key = os.getenv('MISTRAL_API_KEY'),temperature= 0.2)

def formate_doc(docs):
    return '\n\n'.join([doc.page_content for doc in docs])

def retrive_and_rerank(question,retriver):
    docs = retriver.invoke(question)

    reranked_docs = rerank_documents(
        question = question,
        docs = docs,
        top_k = 3
    )

    return formate_doc(reranked_docs)
# def retrieve_and_rerank(question, retriever):
#     print("=" * 70)
#     print(f"Question: {question}")

#     docs = retriever.invoke(question)

#     print(f"\nRetrieved {len(docs)} documents")

#     print("\n----- Before Reranking -----")
#     for i, doc in enumerate(docs):
#         print(f"\nDoc {i+1}")
#         print(doc.page_content[:150])

#     reranked_docs = rerank_documents(
#         question=question,
#         docs=docs,
#         top_k=3
#     )

#     print("\n----- After Reranking -----")
#     for i, doc in enumerate(reranked_docs):
#         print(f"\nTop {i+1}")
#         print(doc.page_content[:150])

#     return formate_doc(reranked_docs)

def build_rag_chain(transcript:str):
    vector_store = build_vector_store(transcript=transcript)

    retriver = get_retriver(transcript=transcript,vector_store=vector_store,k = 8)

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(

        [(
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ]
    )

    # full LCEL Rag pipeline
    rag_chain = (
        {
            'context':RunnableLambda(
                lambda x: retrive_and_rerank(x,retriver)
            ),
            'question':RunnablePassthrough()
        }
    )| prompt | llm | StrOutputParser()

    return rag_chain

# def load_rag_chain():
#     vector_store = load_vector_store()
#     retriver = get_retriver()

#     llm = get_llm()
#     prompt = ChatPromptTemplate.from_messages([
#         (
#             "system",
#             """You are an expert meeting assistant. Answer the user's question 
# based ONLY on the meeting transcript context provided below.

# If the answer is not found in the context, say: 
# "I could not find this information in the meeting transcript."

# Always be concise and precise. If quoting someone, mention it clearly.

# Context from meeting transcript:
# {context}""",
#         ),
#         ("human", "{question}"),
#     ])

#     rag_chain = (
#             {
#                 'context':retriver | RunnableLambda(formate_doc),
#                 'question':RunnablePassthrough()
#             }
#         )| prompt | llm | StrOutputParser()

#     return rag_chain

def ask_question(rag_chain,question:str)-> str:
    print(f'Question: {question}')
    answer = rag_chain.invoke(question)
    print(f'Answer: {answer}')
    return answer