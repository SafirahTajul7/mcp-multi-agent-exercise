# MCP Multi-Server Agent Exercise

A multi-server **Model Context Protocol (MCP)** agent built with LangChain and Google Gemini 2.5 Flash. This project demonstrates how to orchestrate multiple MCP tool servers using different transport protocols (stdio and streamable HTTP).

## Architecture

```
┌─────────────────────────────────────────────┐
│              main.py (Agent)                │
│         Gemini 2.5 Flash + LangChain        │
├─────────────┬───────────────────────────────┤
│   stdio     │      streamable_http          │
├─────────────┼───────────────────────────────┤
│ random_num  │  roll_dice (localhost:8000)    │
│ server      │  server                       │
└─────────────┴───────────────────────────────┘
```

## MCP Servers

| Server | Transport | Tool | Description |
|--------|-----------|------|-------------|
| `random_number` | stdio | `get_number` | Generates a random number (1-100) |
| `roll_dice` | streamable HTTP | `roll_dice_random` | Rolls N 6-sided dice |

## Project Structure

```
mcp/
├── backend/
│   ├── main.py                      # Main agent pipeline
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # API keys (not committed)
│   └── server/
│       ├── http/
│       │   └── roll_dice.py         # HTTP MCP server (dice roller)
│       └── stdio/
│           └── random_number.py     # Stdio MCP server (random number)
├── frontend/                        # (Future use)
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.12+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/apikey))

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SafirahTajul7/mcp-multi-agent-exercise.git
   cd mcp-multi-agent-exercise
   ```

2. **Create virtual environment**
   ```bash
   cd backend
   python -m venv myenv
   myenv\Scripts\activate     # Windows
   # source myenv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** in the `backend/` folder
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Running

You need **2 terminals**:

**Terminal 1** — Start the Roll Dice HTTP server:
```bash
cd backend
python server/http/roll_dice.py
```
Wait until you see: `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2** — Run the agent:
```bash
cd backend
python main.py
```

## Sample Output

```
Connecting to MCP servers...
Fetching tool schemas in parallel...
Connected! Loaded 2 tools.
 - Ready: get_number
 - Ready: roll_dice_random

User: Roll 2 dice for me until you get 6 for both, then let me know how many times.
 Thinking...

==================================================
Final Response:
==================================================
I rolled the dice 4 times before getting 6 for both!
==================================================
```

## Tech Stack

- **LLM**: Google Gemini 2.5 Flash
- **Framework**: LangChain + LangGraph
- **Protocol**: Model Context Protocol (MCP)
- **MCP Adapters**: langchain-mcp-adapters
- **Transports**: stdio, streamable HTTP (FastMCP + Uvicorn)
- **Resilience**: Tenacity (exponential backoff retry)
