import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class AgentState(TypedDict):
    query: str
    context: str
    draft: str
    feedback: str
    status: str

# Initialize DB and LLM
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = Chroma(
    persist_directory="./chroma_data",
    embedding_function=embeddings
)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

def researcher(state: AgentState):
    query = state["query"]
    feedback = state.get("feedback", "")
    
    # Retrieve context
    docs = vector_store.similarity_search(query, k=2)
    context = "\n".join([doc.page_content for doc in docs])
    
    # Prompt LLM
    prompt = f"Answer the following query based ONLY on the provided context.\nQuery: {query}\nContext: {context}\n"
    if feedback:
        prompt += f"Previous feedback to incorporate: {feedback}\n"
        
    response = llm.invoke(prompt)
    
    return {"context": context, "draft": response.content}

def critic(state: AgentState):
    draft = state["draft"]
    context = state["context"]
    
    prompt = f"Verify if the following draft accurately answers the query based on the context.\nContext: {context}\nDraft: {draft}\n"
    prompt += "Output EXACTLY 'APPROVED' if accurate, or 'REJECTED: <reason>' if inaccurate."
    
    response = llm.invoke(prompt)
    output = response.content.strip()
    
    if output.startswith("APPROVED"):
        return {"status": "APPROVED", "feedback": ""}
    else:
        # Extract reason
        reason = output.replace("REJECTED:", "").strip()
        return {"status": "REJECTED", "feedback": reason}

def route_critic(state: AgentState):
    status = state["status"]
    if status == "APPROVED":
        return END
    return "researcher"

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("researcher", researcher)
builder.add_node("critic", critic)
builder.set_entry_point("researcher")
builder.add_edge("researcher", "critic")
builder.add_conditional_edges("critic", route_critic, {END: END, "researcher": "researcher"})
app_graph = builder.compile()

@app.post("/orchestrate")
async def orchestrate(req: QueryRequest):
    initial_state = {
        "query": req.query,
        "context": "",
        "draft": "",
        "feedback": "",
        "status": "pending"
    }
    result = app_graph.invoke(initial_state)
    return result

@app.get("/health/agent")
async def health_agent():
    return {"status": "System Online: LangGraph and Gemini are connected."}

@app.get("/health/rag")
async def health_rag():
    docs = vector_store.similarity_search("What is the dental insurance coverage?", k=1)
    if docs:
        return {"retrieved_fact": docs[0].page_content}
    return {"retrieved_fact": "No document found"}
