from pydantic import BaseModel


class AnalyzeResponse(BaseModel):

    title: str

    summary: str

    action_items: str

    key_decisions: str

    open_questions: str

    transcript : str


class ChatResponse(BaseModel):

    question: str

    answer: str