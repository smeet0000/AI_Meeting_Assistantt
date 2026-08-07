from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain

from api.services.rag_session import save_chain


def run_pipeline(source: str, language: str = "english"):

    print("Starting AI Video Assistant...")

    chunks = process_input(source)

    transcript = transcribe_all(chunks, language)

    title = generate_title(transcript)

    summary = summarize(transcript)

    action_items = extract_action_items(transcript)

    key_decisions = extract_key_decisions(transcript)

    open_questions = extract_questions(transcript)

    rag_chain = build_rag_chain(transcript)

    save_chain(
        session_id="default",
        rag_chain=rag_chain
    )

    print("RAG Chain Saved Successfully")

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": key_decisions,
        "open_questions": open_questions,
    }

   