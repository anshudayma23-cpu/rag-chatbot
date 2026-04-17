"""
Flask web application for HDFC Mutual Fund RAG Chatbot.
Provides REST API and serves the HTML UI.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "retrieval"))

from retrieval.main import RAGSystem
from retrieval.shared_state import shared_state

app = Flask(__name__, template_folder=".", static_folder=".")
CORS(app)

# Store RAG instances by session ID
rag_instances = {}


def get_rag_for_session(session_id: str = None) -> tuple[RAGSystem, str]:
    """Get or create RAG instance for session."""
    if session_id and session_id in rag_instances:
        return rag_instances[session_id], session_id
    
    # Create new instance using shared components
    rag = RAGSystem(session_id=session_id, use_shared=True)
    sid = rag.session_id
    rag_instances[sid] = rag
    return rag, sid


@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    data = request.json
    query = data.get("message", "").strip()
    session_id = data.get("session_id")
    
    if not query:
        return jsonify({"error": "Empty message"}), 400
    
    try:
        rag, sid = get_rag_for_session(session_id)
        response = rag.handle_query(query, session_id=sid)
        
        return jsonify({
            "response": response,
            "session_id": sid,
            "history": rag.get_conversation_history(limit=5)
        })
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """Get conversation history for a session."""
    session_id = request.args.get("session_id")
    limit = request.args.get("limit", 10, type=int)
    
    if not session_id or session_id not in rag_instances:
        return jsonify({"error": "Session not found"}), 404
    
    rag = rag_instances[session_id]
    return jsonify({
        "session_id": session_id,
        "history": rag.get_conversation_history(limit=limit)
    })


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Clear conversation history."""
    data = request.json
    session_id = data.get("session_id")
    
    if not session_id or session_id not in rag_instances:
        return jsonify({"error": "Session not found"}), 404
    
    rag = rag_instances[session_id]
    rag.clear_conversation()
    
    return jsonify({
        "message": "Conversation cleared",
        "session_id": session_id
    })


@app.route("/api/export", methods=["GET"])
def export_chat():
    """Export conversation to file."""
    session_id = request.args.get("session_id")
    fmt = request.args.get("format", "markdown")
    
    if not session_id or session_id not in rag_instances:
        return jsonify({"error": "Session not found"}), 404
    
    rag = rag_instances[session_id]
    try:
        filepath = rag.export_conversation(format=fmt)
        return jsonify({
            "message": f"Exported to {filepath}",
            "filepath": filepath
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Pre-initialize shared state to eliminate first-request latency
# This runs when the module is imported (e.g., by gunicorn)
shared_state.initialize()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f"HDFC Mutual Fund RAG Chatbot - Running on port {port}")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=False)
