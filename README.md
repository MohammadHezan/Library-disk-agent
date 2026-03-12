# Library Desk Agent 📚

An AI-powered library desk assistant with a chat interface. The agent can search books, create orders, manage inventory, and check order status — all backed by a SQLite database and powered by LangChain + LangGraph.

## Project Structure

```
library-agent/
├── app/
│   └── chatUI.html          # Chat UI (sessions, messages)
├── db/
│   └── tables.sql            # Database schema
│   └── seed.sql              # Seed data (10 books, 6 customers, 4 orders)
├── prompts/
│   └── system-prompts.txt    # Agent system prompt
├── server/
│   ├── main.py               # FastAPI server + endpoints
│   ├── agent.py              # LangGraph ReAct agent + tool definitions
│   └── app.py                # SQLite DB access layer
├── .env.example              # Environment config template
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/MohammadHezan/library-agent.git
cd library-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` to choose your LLM provider:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` | `llama3.2:1b` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | — | Required if using OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |

**Using Ollama (default):**
```bash
# Install Ollama: https://ollama.com
ollama pull llama3.2:1b
```

**Using OpenAI:**
```bash
# Set in .env:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
```

### 3. Seed the database

The server auto-creates and seeds the database on first run. To manually reset:

```bash
cd library-agent
rm -f library-agent.db
cd server
python3 -c "from app import init_db; init_db()"
```

### 4. Run the server

```bash
cd server
uvicorn main:app --reload --port 8000
```

### 5. Open the UI

Visit **http://localhost:8000** in your browser.

## Agent Tools

| Tool | Description |
|---|---|
| `find_books(q, by)` | Search books by `title` or `author` (partial match) |
| `create_order(customer_id, items)` | Create an order and reduce stock |
| `restock_book(isbn, qty)` | Add copies to a book's inventory |
| `update_price(isbn, price)` | Change a book's price |
| `order_status(order_id)` | Get order details and total |
| `inventory_summary()` | List low-stock books (stock < 5) |

## Sample Scenarios

**1. Create an order and adjust stock:**
> "We sold 3 copies of Clean Code to customer 2 today. Create the order and adjust stock."

**2. Restock and search:**
> "Restock The Pragmatic Programmer by 10 and list all books by Andrew Hunt."

**3. Check order status:**
> "What's the status of order 3?"

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serve chat UI |
| `POST` | `/chat` | Send message `{session_id, message}` → `{reply}` |
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions` | Create new session |
| `GET` | `/sessions/:id/messages` | Get session messages |
| `DELETE` | `/sessions/:id` | Delete a session |

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Agent:** LangChain + LangGraph (ReAct agent)
- **LLM:** Ollama (local) or OpenAI
- **Database:** SQLite
- **Frontend:** Vanilla HTML/CSS/JS
