"""
Streamlit UI for the AI Video/Meeting Assistant pipeline.

Run with:
    streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.sammarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question



st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎙️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
defaults = {
    "result": None,          # holds pipeline output dict
    "chat_history": [],      # list of (question, answer) tuples
    "processing": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Pipeline runner (mirrors run_pipeline from the original script)
# ---------------------------------------------------------------------------
def run_pipeline(source: str, language: str = "english") -> dict:
    status = st.status("Running pipeline...", expanded=True)

    status.write("📥 Processing input source...")
    chunk = process_input(source=source)

    status.write("📝 Transcribing audio...")
    transcript = transcribe_all(chunk, language=language)

    status.write("🏷️ Generating title...")
    title = generate_title(transcript=transcript)

    status.write("📋 Summarizing transcript...")
    summary = summarize(transcript=transcript)

    status.write("✅ Extracting action items...")
    action_item = extract_action_items(transcript=transcript)

    status.write("🔑 Extracting key decisions...")
    decision = extract_key_decisions(transcript=transcript)

    status.write("❓ Extracting open questions...")
    question = extract_questions(transcript=transcript)

    status.write("🤖 Building RAG chain for chat...")
    rag_chain = build_rag_chain(transcript=transcript)

    status.update(label="Done!", state="complete", expanded=False)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_item": action_item,
        "key_decision": decision,
        "open_question": question,
        "rag_chain": rag_chain,
    }


# ---------------------------------------------------------------------------
# Sidebar - inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎙️ AI Video Assistant")
    st.caption("Turn any YouTube video or local recording into a searchable, "
               "chattable meeting brief.")

    source = st.text_input(
        "YouTube URL or local file path",
        placeholder="https://youtube.com/... or /path/to/audio.mp3",
    )

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    run_clicked = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

    if st.session_state.result is not None:
        st.divider()
        if st.button("🔄 Reset / Start Over", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat_history = []
            st.rerun()

# ---------------------------------------------------------------------------
# Trigger pipeline run
# ---------------------------------------------------------------------------
if run_clicked:
    if not source.strip():
        st.sidebar.error("Please enter a YouTube URL or file path.")
    else:
        try:
            st.session_state.result = run_pipeline(source.strip(), language)
            st.session_state.chat_history = []
        except Exception as e:
            st.sidebar.error(f"Pipeline failed: {e}")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
result = st.session_state.result

if result is None:
    st.title("Welcome 👋")
    st.info(
        "Enter a YouTube URL or a local file path in the sidebar and click "
        "**Run Pipeline** to get started. You'll get a title, summary, "
        "action items, key decisions, open questions, and a chat assistant "
        "for the meeting/video."
    )
else:
    st.title(f"📌 {result['title']}")

    tab_summary, tab_transcript, tab_chat = st.tabs(
        ["📋 Summary & Insights", "📝 Full Transcript", "💬 Chat"]
    )

    # ---------------- Summary tab ----------------
    with tab_summary:
        st.subheader("📋 Summary")
        st.write(result["summary"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("✅ Action Items")
            st.write(result["action_item"])

        with col2:
            st.subheader("🔑 Key Decisions")
            st.write(result["key_decision"])

        with col3:
            st.subheader("❓ Open Questions")
            st.write(result["open_question"])

    # ---------------- Transcript tab ----------------
    with tab_transcript:
        st.subheader("📝 Full Transcript")
        st.text_area(
            "Transcript",
            value=result["transcript"],
            height=500,
            label_visibility="collapsed",
        )
        st.download_button(
            "⬇️ Download Transcript",
            data=result["transcript"],
            file_name="transcript.txt",
            mime="text/plain",
        )

    # ---------------- Chat tab ----------------
    with tab_chat:
        st.subheader("💬 Chat with your meeting")

        for q, a in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                st.write(a)

        question = st.chat_input("Ask something about this meeting/video...")

        if question:
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        answer = ask_question(result["rag_chain"], question)
                    except Exception as e:
                        answer = f"⚠️ Error answering question: {e}"
                st.write(answer)

            st.session_state.chat_history.append((question, answer))