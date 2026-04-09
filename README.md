# Multi-Agent Corporate Logic & Documentation Orchestrator

## 1. Project Objective
This project provides a stateful, multi-agent orchestrator built to analyze complex corporate and legal documents. Specifically designed to handle large-scale financial filings like a Tesla 10-K financial report, this system utilizes advanced AI agents to extract accurate insights, fact-check responses, and eliminate hallucinations. The multi-agent workflow ensures highly reliable data retrieval and verification crucial for finance operations, compliance auditing, and legal reviews.

## 2. Architecture & Technical Stack
The system is built on a modern AI architecture combining generative models, vector search, and a stateful graphing module.

- **FastAPI:** Acts as the backend API wrapper for the entire system, exposing resilient endpoints to trigger document parsing and agent workflows.
- **LangGraph:** The stateful orchestration engine. We implemented a cyclic verification loop:
  - **The Researcher:** Uses Retrieval-Augmented Generation (RAG) to query the vector database and draft an initial response to the user's prompt based solely on extracted facts.
  - **The Critic:** Acts as a quality assurance check, rigorously verifying the Researcher's draft against the context. If hallucinations or inaccuracies are detected, the draft is rejected and routed back to the Researcher with specific feedback for revision.
- **ChromaDB:** A fast, local vector database acting as long-term memory for embeddings of the dense financial documents.
- **Streamlit:** A lightweight, ChatGPT-style frontend chat interface that interacts with the FastAPI backend, preserving conversation history and exposing the AI's research context in real-time.

## 3. File Structure & Code Deep Dive

The repository is modular and separated into dedicated functional bounds:

### `main.py`
The orchestration layer. 
- Defines the `AgentState` schema to enforce strict RAG state (recording `query`, `context`, `draft`, `feedback`, and `status`).
- Contains the LangGraph node logic for the **Researcher** and the **Critic**, as well as the **Conditional Edges** that route execution either toward `END` (if the draft is verified) or back to the Researcher (if rejected). 
- Exposes the `/orchestrate` POST endpoint to ingest queries and trigger graph execution.

### `init_db.py`
The RAG pipeline and ingestion module. 
- Uses `PyPDFLoader` to parse heavily formatted corporate documents (e.g., the 10-K report).
- Applies a `RecursiveCharacterTextSplitter` chunking strategy to divide the text logically while maintaining semantic value.
- Generates high-quality vector representations utilizing the chosen embedding process and populates the local ChromaDB.

### `ui.py`
The frontend presentation layer.
- Maintains user session state for seamless chat history using `st.session_state`.
- Connects asynchronously to the FastAPI backend via POST requests, formatting user input into JSON.
- Displays both the AI assistant's final draft and a collapsible expander containing the verified context used to formulate the answer.

## 4. Key Engineering Decisions

During development, we solved two critical engineering bottlenecks to ensure stability in production environments:

- **The SQLite3 Compatibility Fix:** ChromaDB requires modern SQLite dependencies which are often absent or outdated on standard Linux virtual machines. We integrated a proactive patch by importing `pysqlite3-binary` and mapping it entirely onto `sys.modules['sqlite3']` at runtime, ensuring vector operations proceed flawlessly across any distribution.
- **API Rate Limit Batching:** When chunking and embedding a massive, 100+ page 10-K PDF, rapid continuous requests risk triggering `429 RESOURCE_EXHAUSTED` errors from API providers. To respect free-tier quotas and prevent fatal crashes, we structured the ingestion loop to process text in batched segments with intentional 60-second sleep intervals, optimizing for stability over arbitrary speed.



## 5. Local Setup & Deployment (Docker Recommended)

This repository comes pre-trained with a vector database (`chroma_data`) containing a parsed Tesla 10-K financial report. **No initial ingestion is required** to run queries out of the box.

### The "Zero-Friction" Quick Start
1. **Credentials:** Rename the `.env.example` file to `.env` and insert your Gemini API key.
2. **Launch:** Open your terminal in the project root and run:
   `docker compose up --build`
3. **Access:** Navigate to `http://localhost:8501` in your web browser to interact with the UI.

### How to Train on Your Own Custom Data
Want the AI to analyze a different document (e.g., a textbook, legal contract, or HR manual)? 
1. Drop your new PDF into the root directory.
2. Open `init_db.py` and change the target filename on this line:
   `loader = PyPDFLoader("tesla_10k.pdf")` -> `loader = PyPDFLoader("your_new_file.pdf")`
3. Delete the existing `chroma_data` folder to clear the AI's old memory.
4. Run the ingestion script inside the Docker container to build the new database:
   `docker compose run backend python init_db.py`
5. Once it finishes, restart your containers. The AI Council is now an expert on your new document!