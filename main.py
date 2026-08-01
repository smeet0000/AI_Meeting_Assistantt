from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize,generate_title
from core.extractor import extract_action_items,extract_key_decisions,extract_questions
from core.rag_engine import build_rag_chain,ask_question
import os


# print('KEY LOADED:',os.getenv('SARVAM_API_KEY'))
# print('CWD: ',os.getcwd())

def run_pipeline(source: str,language:str ='english')-> dict:
    print('starting AI video Assistant')

    chunk = process_input(source=source)

    transcript = transcribe_all(chunk,language=language)
    print(f'raw transcription (first 300 character) {transcript[:300]}')

    title = generate_title(transcript=transcript)

    summary = summarize(transcript=transcript)

    action_item = extract_action_items(transcript=transcript)

    decision = extract_key_decisions(transcript=transcript)

    question = extract_questions(transcript=transcript)

    rag_chain = build_rag_chain(transcript=transcript)

    return {
        'title':title,
        'transcipt':transcript,
        'summary':summary,
        'action_item':action_item,
        'key_decision':decision,
        'open_question':question,
        'rag_chain':rag_chain,
    }

if __name__ == '__main__':
     # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_item']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decision']}")
    print(f"\n❓ Open Questions:\n{result['open_question']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n🤖 Assistant: {answer}\n")
