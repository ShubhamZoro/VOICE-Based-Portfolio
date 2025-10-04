# common/agent_functions.py
from .rag_store import get_store

# --- RAG tool ---
async def retrieve_context(params):
    query = params.get("query", "")
    k = int(params.get("k", 5))
    if not query.strip():
        return {"error": "query is required"}
    store = get_store()
    hits = store.retrieve(query, k=k)
    results = [
        {"chunk_id": c.meta["chunk_id"], "score": round(score, 4), "text": c.text}
        for (c, score) in hits if score > 0
    ]
    return {"query": query, "results": results}

# --- (optional) filler + farewell for proper protocol with agent ---
async def agent_filler(websocket, params):
    msg_type = params.get("message_type", "lookup")
    inject_message = {"type": "InjectAgentMessage",
                      "message": "Let me pull that from the document..." if msg_type=="lookup" else "One moment..."}
    return {"function_response": {"status": "queued", "message_type": msg_type},
            "inject_message": inject_message}

async def end_call(websocket, params):
    farewell_type = params.get("farewell_type", "general")
    text = "Thanks! Bye." if farewell_type=="thanks" else "Goodbye!"
    return {"function_response": {"status": "closing", "message": text},
            "inject_message": {"type": "InjectAgentMessage", "message": text},
            "close_message": {"type": "close"}}

# --- schema sent to Deepgram ---
FUNCTION_DEFINITIONS = [
    {
        "name": "retrieve_context",
        "description": "Fetch the most relevant passages from Shubham's DOCX. MUST be called before answering any user question.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "User's question"},
                "k": {"type": "number", "description": "Top-k passages (default 5)"}
            },
            "required": ["query"]
        },
    },
    {
        "name": "agent_filler",
        "description": "Use before looking up info to provide brief filler.",
        "parameters": {
            "type": "object",
            "properties": {
                "message_type": {"type": "string", "enum": ["lookup","general"]}
            },
            "required": ["message_type"]
        },
    },
    {
        "name": "end_call",
        "description": "End conversation and close connection.",
        "parameters": {
            "type": "object",
            "properties": {
                "farewell_type": {"type": "string", "enum": ["thanks","general","help"]}
            },
            "required": ["farewell_type"]
        },
    },
]

FUNCTION_MAP = {
    "retrieve_context": retrieve_context,
    "agent_filler": agent_filler,
    "end_call": end_call,
}
