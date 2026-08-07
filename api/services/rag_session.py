rag_sessions = {}


def save_chain(session_id, rag_chain):
    rag_sessions[session_id] = rag_chain


def get_chain(session_id):
    return rag_sessions.get(session_id)


def delete_chain(session_id):
    rag_sessions.pop(session_id, None)