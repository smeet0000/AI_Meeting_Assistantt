import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Form

from api.schemas.analyze import AnalyzeRequest
from api.schemas.responses import AnalyzeResponse
from api.services.pipeline import run_pipeline
from api.exceptions import PipelineException

from api.core.logger import logger


router = APIRouter(
    prefix="/analyze",
    tags=["Analyze"]
)


# ---------------------------------------------------------
# Analyze YouTube URL
# ---------------------------------------------------------

@router.post(
    "/youtube",
    response_model=AnalyzeResponse
)
def analyze_youtube(request: AnalyzeRequest):

    try:

        logger.info(
            f"Analyzing YouTube URL: {request.source}"
        )

        result = run_pipeline(
            source=request.source,
            language=request.language,
        )

        logger.info(
            "YouTube analysis completed successfully."
        )

        # Debugging
        print("========== YOUTUBE RESULT ==========")
        print(result)

        return {
            "title": result["title"],
            "summary": result["summary"],
            "action_items": result["action_items"],
            "key_decisions": result["key_decisions"],
            "open_questions": result["open_questions"],
            "transcript": result["transcript"],
        }

    except Exception as e:

        logger.error(
            f"YouTube analysis failed: {str(e)}"
        )

        raise PipelineException(
            detail=str(e)
        )


# ---------------------------------------------------------
# Analyze Uploaded File
# ---------------------------------------------------------

@router.post(
    "/file"
)
def analyze_file(
    file: UploadFile = File(...),
    language: str = Form("english")
):

    try:

        # -------------------------------
        # Create upload directory
        # -------------------------------

        upload_dir = "uploads"

        os.makedirs(
            upload_dir,
            exist_ok=True
        )

        # -------------------------------
        # Generate unique filename
        # -------------------------------

        unique_filename = (
            f"{uuid.uuid4().hex}_{file.filename}"
        )

        file_path = os.path.join(
            upload_dir,
            unique_filename
        )

        # -------------------------------
        # Save uploaded file
        # -------------------------------

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        logger.info(
            f"Uploaded File: {unique_filename}"
        )

        print("========== FILE UPLOAD ==========")
        print("File:", file.filename)
        print("Saved:", file_path)
        print("Language:", language)

        # -------------------------------
        # Run AI pipeline
        # -------------------------------

        result = run_pipeline(
            source=file_path,
            language=language,
        )

        logger.info(
            "File analysis completed successfully."
        )

        # -------------------------------
        # Debug result
        # -------------------------------

        print("========== FILE RESULT ==========")
        print(result)

        print("Title:", result["title"])
        print("Summary:", result["summary"])
        print("Action Items:", result["action_items"])
        print("Key Decisions:", result["key_decisions"])
        print("Open Questions:", result["open_questions"])

        # -------------------------------
        # Return result to frontend
        # -------------------------------

        return {
            "title": result["title"],
            "summary": result["summary"],
            "action_items": result["action_items"],
            "key_decisions": result["key_decisions"],
            "open_questions": result["open_questions"],
            "transcript": result["transcript"],
        }

    except Exception as e:

        logger.error(
            f"File analysis failed: {str(e)}"
        )

        raise PipelineException(
            detail=str(e)
        )