"""Local FastAPI interface for the DAT Agent router."""

from functools import lru_cache # least recently used cache for router agent
from threading import Lock
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, ConfigDict, Field

from .orchestrator import create_router_agent, create_state
from .schema import models

app = FastAPI(title="DAT Agent", version="1.0")
# Serialize access to the in-memory checkpointer for this local prototype.
chat_lock = Lock()


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=10000)
    session_id: UUID | None = None
    model: models = "google"


class ChatResponse(BaseModel):
    answer: str
    session_id: UUID
    model: models
    route: str | None = None


@lru_cache(maxsize=1)
def get_router():
    """Create and cache the router agent for the lifetime of the process."""
    return create_router_agent()


@app.get("/health")
def health() -> dict[str, str]:
    """Process liveness only; does not contact providers or PostgreSQL."""
    return {"status": "ok"}


@app.get("/models")
def list_models() -> list[str]:
    """Provider choices, matching the frontend's model selector."""
    return ["google", "openai", "anthropic", "ollama"]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or uuid4()
    config = {"configurable": {"thread_id": str(session_id)}}
    state = create_state(request.question, request.model)
    state.messages = [HumanMessage(content=request.question)]
    try:
        with chat_lock:
            router = get_router()
            result = router.invoke(state, config=config)
            answer = result.get("answer")
            if result.get("error") or not isinstance(answer, str) or not answer.strip():
                raise ValueError("Agent did not produce an answer")
            router.update_state(config, {"messages": [AIMessage(content=answer)]})
    except Exception:
        # Provider exceptions may include credentials, database details or URLs.
        raise HTTPException(status_code=502, detail="The agent could not complete this request. Check your local provider and database configuration.") from None
    return ChatResponse(answer=answer, session_id=session_id, model=request.model, route=result.get("route_to"))
