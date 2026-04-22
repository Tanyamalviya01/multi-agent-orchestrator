import os
import sys
import json
import shutil
import tempfile
from typing import TypedDict, Optional
from dotenv import load_dotenv

if sys.platform.startswith("linux"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from history_db import init_history_db, save_query, get_history

load_dotenv()

app = FastAPI(title="AI Council Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    task: str = "ask"           # ask | summarize | insights | validate
    domain: str = "general"     # general | finance | legal | hr
    plan: str = "free"          # free | premium
    collection: str = "default" # which chroma collection to query

class AgentState(TypedDict):
    query: str
    task: str
    domain: str
    plan: str
    collection: str
    context: str
    draft: str
    summary: str
    insights: str
    feedback: str
    status: str
    confidence: int
    explanation: str

# ─── Domain System Prompts ──────────────────────────────────────────────────────

DOMAIN_PROMPTS = {
    "finance": "You are a financial analyst. Focus on numerical accuracy, fiscal years, GAAP compliance, revenue figures, margins, and cash flow. Always cite specific numbers from the context.",
    "legal":   "You are a legal analyst. Focus on obligations, liabilities, definitions, clauses, and dates. Use precise legal language and flag any ambiguities.",
    "hr":      "You are an HR specialist. Focus on policies, benefits, compliance, headcount, compensation bands, and employee obligations. Be clear and empathetic.",
    "general": "You are an expert analyst. Be thorough, accurate, and cite specific facts from the context.",
}

# ─── LLM + Embeddings ──────────────────────────────────────────────────────────

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def get_vectorstore(collection: str) -> Chroma:
    persist_dir = f"./chroma_data" if collection == "default" else f"./chroma_data/user_{collection}"
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

# ─── Agent Nodes ───────────────────────────────────────────────────────────────

def researcher(state: AgentState) -> dict:
    query    = state["query"]
    feedback = state.get("feedback", "")
    domain   = state.get("domain", "general")
    domain_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["general"])

    try:
        vs   = get_vectorstore(state.get("collection", "default"))
        docs = vs.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception:
        context = "No document context available."

    prompt = (
        f"{domain_prompt}\n\n"
        f"Answer the following query based ONLY on the provided context. "
        f"Do not use outside knowledge.\n\n"
        f"Query: {query}\n\nContext:\n{context}"
    )
    if feedback:
        prompt += f"\n\nPrevious critic feedback to address: {feedback}"

    response = llm.invoke(prompt)
    return {"context": context, "draft": response.content}


def critic(state: AgentState) -> dict:
    draft   = state["draft"]
    context = state["context"]
    query   = state["query"]

    prompt = (
        f"You are a rigorous fact-checker. Verify whether the draft accurately answers "
        f"the query using ONLY the provided context. Check for hallucinations, unsupported claims, "
        f"and missing key information.\n\n"
        f"Query: {query}\nContext:\n{context}\nDraft:\n{draft}\n\n"
        f"Respond in this EXACT JSON format (no markdown, no backticks):\n"
        f'{{"status": "APPROVED" or "REJECTED", "confidence": <0-100 integer>, '
        f'"reason": "<brief explanation>"}}'
    )

    response = llm.invoke(prompt)
    raw = response.content.strip()

    try:
        # strip any accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        status     = data.get("status", "REJECTED")
        confidence = int(data.get("confidence", 50))
        reason     = data.get("reason", "")
    except Exception:
        # fallback parse
        status     = "APPROVED" if "APPROVED" in raw else "REJECTED"
        confidence = 75 if status == "APPROVED" else 40
        reason     = raw

    if status == "APPROVED":
        return {"status": "APPROVED", "confidence": confidence, "feedback": "", "explanation": reason}
    else:
        return {"status": "REJECTED", "confidence": confidence, "feedback": reason, "explanation": reason}


def summarizer(state: AgentState) -> dict:
    context = state["context"]
    domain  = state.get("domain", "general")
    domain_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["general"])

    prompt = (
        f"{domain_prompt}\n\n"
        f"Produce a concise, well-structured summary of the following document context. "
        f"Use bullet points for key facts. Max 200 words.\n\nContext:\n{context}"
    )
    response = llm.invoke(prompt)
    return {"summary": response.content, "draft": response.content}


def insight_agent(state: AgentState) -> dict:
    context = state["context"]
    query   = state["query"]
    domain  = state.get("domain", "general")
    domain_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["general"])

    prompt = (
        f"{domain_prompt}\n\n"
        f"You are an expert insight generator. Based on the context below, produce:\n"
        f"1. **Key Trends** – patterns and trajectories you observe\n"
        f"2. **Comparisons** – year-over-year or segment comparisons where applicable\n"
        f"3. **Key Highlights** – the 3 most important takeaways\n"
        f"4. **Risks or Flags** – anything concerning or worth watching\n\n"
        f"Query context: {query}\n\nDocument context:\n{context}"
    )
    response = llm.invoke(prompt)
    return {"insights": response.content, "draft": response.content}


def explain_node(state: AgentState) -> dict:
    context = state["context"]
    draft   = state["draft"]

    prompt = (
        f"Explain in 3 concise bullet points exactly which parts of the source context "
        f"supported each major claim in the answer below. Quote brief phrases from the context.\n\n"
        f"Answer:\n{draft}\n\nSource context:\n{context}"
    )
    response = llm.invoke(prompt)
    return {"explanation": response.content}


# ─── Graph Routing ──────────────────────────────────────────────────────────────

def route_by_task(state: AgentState) -> str:
    task = state.get("task", "ask")
    plan = state.get("plan", "free")
    if task == "summarize":
        return "summarizer"
    if task == "insights":
        if plan != "premium":
            # Inject a polite gate message and route to end via critic
            return "premium_gate"
        return "insight_agent"
    return "researcher"  # ask + validate both start with researcher


def route_critic(state: AgentState) -> str:
    if state.get("status") == "APPROVED":
        task = state.get("task", "ask")
        if task == "ask":
            return "explain"
        return END
    return "researcher"


def premium_gate(state: AgentState) -> dict:
    return {
        "draft": "⭐ This feature is available on the **Premium plan**. Upgrade to unlock advanced insights, trend analysis, and comparisons.",
        "status": "APPROVED",
        "confidence": 100,
        "explanation": "",
        "insights": "",
    }


# ─── Build Graph ────────────────────────────────────────────────────────────────

builder = StateGraph(AgentState)
builder.add_node("researcher",    researcher)
builder.add_node("critic",        critic)
builder.add_node("summarizer",    summarizer)
builder.add_node("insight_agent", insight_agent)
builder.add_node("explain",       explain_node)
builder.add_node("premium_gate",  premium_gate)

builder.set_conditional_entry_point(
    route_by_task,
    {
        "researcher":    "researcher",
        "summarizer":    "summarizer",
        "insight_agent": "insight_agent",
        "premium_gate":  "premium_gate",
    }
)

builder.add_edge("researcher",    "critic")
builder.add_edge("summarizer",    "critic")
builder.add_edge("insight_agent", "critic")
builder.add_edge("premium_gate",  END)

builder.add_conditional_edges(
    "critic",
    route_critic,
    {END: END, "researcher": "researcher", "explain": "explain"}
)
builder.add_edge("explain", END)

app_graph = builder.compile()

# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/orchestrate")
async def orchestrate(req: QueryRequest):
    initial_state: AgentState = {
        "query":      req.query,
        "task":       req.task,
        "domain":     req.domain,
        "plan":       req.plan,
        "collection": req.collection,
        "context":    "",
        "draft":      "",
        "summary":    "",
        "insights":   "",
        "feedback":   "",
        "status":     "pending",
        "confidence": 0,
        "explanation": "",
    }
    result = app_graph.invoke(initial_state, {"recursion_limit": 6})

    # Save to history
    save_query(
        query=req.query,
        task=req.task,
        domain=req.domain,
        draft=result.get("draft", ""),
        confidence=result.get("confidence", 0),
    )

    return result


@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), collection: str = "default"):
    """Upload and ingest a PDF into a named ChromaDB collection."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages  = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks   = splitter.split_documents(pages)

        persist_dir = f"./chroma_data/user_{collection}"
        # Clear old collection if exists
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)

        vs = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

        # Batch to respect rate limits
        batch_size = 80
        for i in range(0, len(chunks), batch_size):
            vs.add_documents(chunks[i:i + batch_size])

        return {
            "status":     "success",
            "pages":      len(pages),
            "chunks":     len(chunks),
            "collection": collection,
        }
    finally:
        os.unlink(tmp_path)


@app.get("/history")
async def query_history(limit: int = 20):
    return get_history(limit=limit)


@app.get("/health/agent")
async def health_agent():
    return {"status": "System Online: LangGraph, 4 agents, and Gemini are connected."}


@app.get("/health/rag")
async def health_rag():
    try:
        vs   = get_vectorstore("default")
        docs = vs.similarity_search("revenue", k=1)
        if docs:
            return {"retrieved_fact": docs[0].page_content[:200]}
    except Exception as e:
        return {"error": str(e)}
    return {"retrieved_fact": "No document found"}


# ─── Init ───────────────────────────────────────────────────────────────────────

init_history_db()
