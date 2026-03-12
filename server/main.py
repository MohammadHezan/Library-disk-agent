from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app import init_db, get_messages, get_sessions
from agent import run_agent
import os, uuid

init_db()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    query: str
    session_id: str = ""

@app.post("/query")
def query(body: ChatRequest):
    sid = body.session_id or str(uuid.uuid4())
    try:
        reply = run_agent(sid, body.query)
    except Exception as e:
        reply = f"Error: {e}"
    return {"response": reply or "No response.", "session_id": sid}

@app.get("/sessions")
def sessions():
    return get_sessions()

@app.get("/sessions/{session_id}")
def messages(session_id: str):
    return get_messages(session_id)

@app.get("/")
def ui():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "chatUI.html")
    return FileResponse(path)
