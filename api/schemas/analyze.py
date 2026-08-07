from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    source : str
    language : str ='english'