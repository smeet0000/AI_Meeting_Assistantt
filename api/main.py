from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.analyze import router as analyze_router
from api.routers.chat import router as chat_router


app = FastAPI(
    title="AI Meeting Assistant API",
    version="1.0"
)


# -------------------------------
# CORS
# -------------------------------

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Routers
# -------------------------------

app.include_router(analyze_router)
app.include_router(chat_router)


# -------------------------------
# Home
# -------------------------------

@app.get("/")
def home():
    return {
        "message": "AI Meeting Assistant API Running"
    }