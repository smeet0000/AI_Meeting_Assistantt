import whisper
import os
import requests
from pydub import AudioSegment


# Sarvam sync STT-translate API rejects audio longer than 30 seconds.
# We slice each chunk into 25-second pieces.
SARVAM_PIECE_SECONDS = 25


WHISPER_MODEL = os.getenv(
    "WHISPER_MODEL",
    "small"
)

SARVAM_API_KEY = os.getenv(
    "SARVAM_API_KEY"
)

SARVAM_STT_TRANSLATE_URL = (
    "https://api.sarvam.ai/speech-to-text-translate"
)

SARVAM_MODEL = os.getenv(
    "SARVAM_STT_MODEL",
    "saaras:v2.5"
)


_model = None


# ---------------------------------------------------------
# Load Whisper model
# ---------------------------------------------------------

def load_model():

    global _model

    if _model is None:

        print(
            f"Loading Whisper model: {WHISPER_MODEL} ..."
        )

        _model = whisper.load_model(
            WHISPER_MODEL
        )

        print("Whisper model loaded.")

    return _model


# ---------------------------------------------------------
# Whisper transcription
# ---------------------------------------------------------

def transcribe_chunk_whisper(
    chunk_path: str
) -> str:

    model = load_model()

    result = model.transcribe(
        chunk_path,
        task="transcribe"
    )

    return result["text"]


# ---------------------------------------------------------
# Send audio piece to Sarvam
# ---------------------------------------------------------

def _send_to_sarvam(
    piece_path: str
) -> str:

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set."
        )

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(
        piece_path,
        "rb"
    ) as f:

        files = {
            "file": (
                os.path.basename(piece_path),
                f,
                "audio/wav"
            )
        }

        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false"
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    if not response.ok:

        print(
            f"\nSarvam returned "
            f"{response.status_code}"
        )

        print(
            f"Response body: "
            f"{response.text}\n"
        )

        response.raise_for_status()

    return response.json().get(
        "transcript",
        ""
    )


# ---------------------------------------------------------
# Sarvam transcription
# ---------------------------------------------------------

def transcribe_chunk_sarvam(
    chunk_path: str
) -> str:

    """
    Sarvam sync API accepts <= 30 seconds.

    Each chunk is split into 25-second pieces,
    sent separately, and then joined.
    """

    if not SARVAM_API_KEY:

        raise RuntimeError(
            "SARVAM_API_KEY is not set "
            "in environment / .env"
        )

    audio = AudioSegment.from_wav(
        chunk_path
    )

    piece_ms = (
        SARVAM_PIECE_SECONDS * 1000
    )

    full_text = ""

    total_pieces = (
        len(audio) + piece_ms - 1
    ) // piece_ms

    for i, start in enumerate(
        range(
            0,
            len(audio),
            piece_ms
        )
    ):

        piece = audio[
            start:start + piece_ms
        ]

        piece_path = (
            f"{chunk_path}_sv_{i}.wav"
        )

        piece.export(
            piece_path,
            format="wav"
        )

        try:

            print(
                f"  → Sarvam piece "
                f"{i + 1}/{total_pieces} ..."
            )

            full_text += (
                _send_to_sarvam(
                    piece_path
                )
                + " "
            )

        finally:

            if os.path.exists(
                piece_path
            ):
                os.remove(
                    piece_path
                )

    return full_text.strip()


# ---------------------------------------------------------
# Transcribe one chunk
# ---------------------------------------------------------

def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:

    """
    english  → Whisper
    hinglish → Sarvam
    """

    if language.lower() == "hinglish":

        return transcribe_chunk_sarvam(
            chunk_path
        )

    return transcribe_chunk_whisper(
        chunk_path
    )


# ---------------------------------------------------------
# Transcribe all chunks
# ---------------------------------------------------------

def transcribe_all(
    chunks: list,
    language: str = "english"
) -> str:

    full_transcript = ""

    engine = (
        "Sarvam AI"
        if language.lower() == "hinglish"
        else "Whisper"
    )

    print(
        f"Using {engine} for transcription."
    )

    for i, chunk in enumerate(chunks):

        print(
            f"Transcribing chunk "
            f"{i + 1}/{len(chunks)}..."
        )

        text = transcribe_chunk(
            chunk,
            language=language
        )

        full_transcript += (
            text + " "
        )

    print(
        "Transcription complete."
    )

    return full_transcript.strip()