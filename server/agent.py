"""
Library Desk Agent – LangChain + LangGraph ReAct agent with tools.
"""
import json
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app import (
    find_books as _find_books,
    create_order as _create_order,
    restock_book as _restock_book,
    update_price as _update_price,
    order_status as _order_status,
    inventory_summary as _inventory_summary,
    save_message,
    save_tool_call,
    get_messages,
)

# ── LLM selection ────────────────────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()


def _build_llm():
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
            temperature=0,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )


# ── tools ────────────────────────────────────────────────────────────────

@tool
def find_books(q: str, by: str = "title") -> str:
    """Search for books by title or author (partial match).

    Args:
        q: The search query string.
        by: Field to search – "title" or "author".
    """
    return json.dumps(_find_books(q=q, by=by), indent=2)


@tool
def create_order(customer_id: int, items: list[dict]) -> str:
    """Create a customer order and reduce book stock.

    Args:
        customer_id: The customer's ID number.
        items: List of dicts, each with "isbn" (str) and "qty" (int).
    """
    return json.dumps(_create_order(customer_id=customer_id, items=items), indent=2)


@tool
def restock_book(isbn: str, qty: int) -> str:
    """Add copies to a book's inventory.

    Args:
        isbn: The ISBN of the book.
        qty: Number of copies to add.
    """
    return json.dumps(_restock_book(isbn=isbn, qty=qty), indent=2)


@tool
def update_price(isbn: str, price: float) -> str:
    """Change the listed price of a book.

    Args:
        isbn: The ISBN of the book.
        price: The new price in dollars.
    """
    return json.dumps(_update_price(isbn=isbn, price=price), indent=2)


@tool
def order_status(order_id: int) -> str:
    """Look up the status and details of an existing order.

    Args:
        order_id: The order ID to look up.
    """
    return json.dumps(_order_status(order_id=order_id), indent=2)


@tool
def inventory_summary() -> str:
    """Return an inventory report highlighting low-stock books (stock < 5)."""
    return json.dumps(_inventory_summary(), indent=2)


TOOLS = [find_books, create_order, restock_book, update_price, order_status, inventory_summary]

# ── system prompt ────────────────────────────────────────────────────────

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "system-prompts.txt")


def _load_system_prompt() -> str:
    with open(PROMPT_PATH) as f:
        return f.read().strip()


# ── agent ────────────────────────────────────────────────────────────────

_llm = _build_llm()
_agent = create_react_agent(model=_llm, tools=TOOLS)


def run_agent(session_id: str, user_message: str) -> str:
    """
    Send a user message through the agent, persist to DB, return assistant reply.
    """
    save_message(session_id, "user", user_message)

    # Build conversation history from DB
    history = get_messages(session_id)
    lc_messages = [{"role": "system", "content": _load_system_prompt()}]
    for m in history:
        if m["role"] in ("user", "assistant"):
            lc_messages.append({"role": m["role"], "content": m["content"]})

    # Invoke agent
    result = _agent.invoke({"messages": lc_messages})
    messages = result.get("messages", [])

    # Log tool calls
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                save_tool_call(session_id, tc["name"], json.dumps(tc.get("args", {})), "")
        if hasattr(msg, "type") and msg.type == "tool":
            save_tool_call(
                session_id,
                getattr(msg, "name", "unknown"),
                "",
                msg.content if isinstance(msg.content, str) else json.dumps(msg.content),
            )

    # Extract final reply – walk backwards to find last AI message with real content
    assistant_reply = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai":
            content = msg.content
            # content can be str, list, or None
            if isinstance(content, list):
                # Extract text parts from list-style content
                parts = [p if isinstance(p, str) else p.get("text", "") for p in content]
                content = "\n".join(p for p in parts if p)
            if content:
                assistant_reply = content
                break

    if not assistant_reply:
        # Fallback: try to find any tool result to summarise
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "tool" and msg.content:
                assistant_reply = f"Tool result: {msg.content}"
                break

    if not assistant_reply:
        assistant_reply = "I'm sorry, I couldn't generate a response. Please try rephrasing your question."

    save_message(session_id, "assistant", assistant_reply)
    return assistant_reply
