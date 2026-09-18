"""
FastAPI routes for the chat API.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

import json
import os
from typing import Optional
from app.core.config import settings, set_use_local_ai_setting, set_ai_provider_setting
from app.postgres_database.database import get_db
from app.postgres_database import crud
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetail,
    SessionTitleUpdate,
    AISettingsResponse,
    AISettingsUpdate,
)
from app.services.rag_service import generate_chat_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# AI Provider Settings endpoints
# ---------------------------------------------------------------------------

@router.get("/settings", response_model=AISettingsResponse)
def get_ai_settings():
    """Get current AI provider settings."""
    provider = getattr(settings, "AI_PROVIDER", "groq" if settings.GROQ_API_KEY else "local").lower()
    if provider == "groq":
        active_model = settings.GROQ_MODEL
    elif provider == "local":
        active_model = settings.CHAT_MODEL
    else:
        active_model = "gpt-4o-mini"

    return AISettingsResponse(
        ai_provider=provider,
        use_local_ai=(provider == "local"),
        chat_model=active_model,
        local_model=settings.CHAT_MODEL,
        groq_model=settings.GROQ_MODEL,
        cloud_model="gpt-4o-mini",
        has_groq_key=bool(settings.GROQ_API_KEY),
        has_openai_key=bool(settings.OPENAI_API_KEY),
    )


@router.post("/settings", response_model=AISettingsResponse)
def update_ai_settings(body: AISettingsUpdate):
    """Update active AI provider (Local AI vs Groq vs ChatGPT) in memory and on disk .env."""
    if body.ai_provider:
        set_ai_provider_setting(body.ai_provider)
    elif body.use_local_ai is not None:
        set_use_local_ai_setting(body.use_local_ai)
    return get_ai_settings()



@router.get("/workspaces")
def get_workspaces():
    """
    Returns the dynamic list of workspaces and automation inventory statistics:
    total_automations = total_folders - 2 (excluding General and Infrastructure).
    """
    base_dir = getattr(settings, "BASE_DOCUMENTS_FOLDER", r"C:\Users\P128F5F\OneDrive - Ceridian HCM Inc\Desktop\AutomationFiles")
    folders = []
    if os.path.exists(base_dir):
        folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

    total_folders = len(folders)
    total_automations = max(0, total_folders - 2) if "Infrastructure" in folders else max(0, total_folders - 1)

    workspace_catalog = [
        {"id": "ROE", "name": "Record of Employment (ROE)", "desc": "Isolate queries to ROE", "is_automation": True},
        {"id": "Overpayment", "name": "Overpayment Support", "desc": "Isolate queries to Overpayment", "is_automation": True},
        {"id": "SyncPay", "name": "SyncPay Support", "desc": "Isolate queries to SyncPay", "is_automation": True},
        {"id": "Monthly Hourly Update", "name": "Monthly Hourly Update (MHU)", "desc": "Revenue allocation & hourly updates", "is_automation": True},
        {"id": "Invoice Supplimental Details", "name": "Invoice Supplemental Details (ISD)", "desc": "Invoicing & billing reports", "is_automation": True},
        {"id": "Infrastructure", "name": "Infrastructure Support", "desc": "VMs, bot machines & servers", "is_automation": False},
        {"id": "General", "name": "General Support", "desc": "Query all repository documents", "is_automation": False},
    ]

    return {
        "total_folders": total_folders,
        "total_automations": total_automations,
        "formula": "total_automations = total_folders - 2 (general and infra docs)",
        "folders": folders,
        "workspaces": workspace_catalog
    }


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    body: ChatSessionCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """Create a new chat session linked to the current user."""
    user_id = body.user_id or x_user_id
    session = crud.create_session(db, title=body.title, automation=body.automation, user_id=user_id)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """List chat sessions for the current user (most recent first)."""
    return crud.get_all_sessions(db, user_id=x_user_id)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(
    session_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """Get a session with its full message history."""
    session = crud.get_session(db, session_id, user_id=x_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}/title", response_model=ChatSessionResponse)
def rename_session(
    session_id: str,
    body: SessionTitleUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """Rename a chat session."""
    session = crud.update_session_title(db, session_id, body.title, user_id=x_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    deleted = crud.delete_session(db, session_id, user_id=x_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


# ---------------------------------------------------------------------------
# Chat / RAG endpoint
# ---------------------------------------------------------------------------

import re

def _detect_workspace(content: str, session_automation: Optional[str]) -> tuple[Optional[str], bool]:
    """
    Helper to detect workspace from message content or fallback to session's saved workspace.
    Returns (matched_automation, is_switch_requested)
    """
    content_lower = content.lower()
    is_switch_requested = any(phrase in content_lower for phrase in [
        "switch workspace", "change workspace", "select workspace", 
        "choose workspace", "switch automation", "change automation"
    ])
    
    matched_automation = None
    if not is_switch_requested:
        if re.search(r"\b(roe|record of employment)\b", content_lower):
            matched_automation = "ROE"
        elif re.search(r"\b(overpayment|overpayments)\b", content_lower):
            matched_automation = "Overpayment"
        elif re.search(r"\b(syncpay|sync pay|sync-pay|amex)\b", content_lower):
            matched_automation = "SyncPay"
        elif re.search(r"\b(mhu|monthly hourly update|monthly hourly|revenue allocation)\b", content_lower):
            matched_automation = "Monthly Hourly Update"
        elif re.search(r"\b(invoice|invoices|isd|supplemental details|supplimental details)\b", content_lower):
            matched_automation = "Invoice Supplimental Details"
        elif re.search(r"\b(infrastructure|infra|vm|vms|vm's|vms'|virtual machine|virtual machines|server|servers|ip address|machine|machines)\b", content_lower):
            matched_automation = "Infrastructure"
        elif "general" in content_lower:
            matched_automation = "General"

    # If no explicit workspace mentioned in message and no switch requested, reuse session workspace
    if matched_automation is None and not is_switch_requested and session_automation:
        matched_automation = session_automation

    return matched_automation, is_switch_requested


@router.post("/sessions/{session_id}/message", response_model=ChatResponse)
def send_message(
    session_id: str,
    body: ChatMessageRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Send a user message, run the RAG pipeline, and return both the
    saved user message and the AI-generated response.
    """
    # Verify session exists and belongs to current user
    session = crud.get_session(db, session_id, user_id=x_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save the user's message
    user_msg = crud.add_message(db, session_id, role="user", content=body.message)

    # Infer workspace from current message content or existing session workspace
    matched_automation, is_switch_requested = _detect_workspace(body.message, session.automation)

    # If no workspace matched, return the selection prompt for this message
    if matched_automation is None:
        prompt_content = "[AUTOMATION_SELECT] Select which automation workspace this question is for:"
        ai_msg = crud.add_message(db, session_id, role="assistant", content=prompt_content)
        
        # Auto-title the session on the first message
        prior_messages = crud.get_session_messages(db, session_id)
        if len(prior_messages) <= 2:
            auto_title = body.message[:50] + ("..." if len(body.message) > 50 else "")
            crud.update_session_title(db, session_id, auto_title)
            
        return ChatResponse(
            session_id=session_id,
            user_message=ChatMessageResponse.model_validate(user_msg),
            ai_message=ChatMessageResponse.model_validate(ai_msg),
        )

    # Save/lock session workspace in DB for subsequent chat messages
    crud.update_session_automation(db, session_id, matched_automation)

    # Build conversation history from prior messages (for context continuity)
    prior_messages = crud.get_session_messages(db, session_id)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in prior_messages
        if msg.id != user_msg.id and not msg.content.startswith("[AUTOMATION_SELECT")
    ]

    # Run RAG pipeline with dynamically inferred or saved session automation scope
    try:
        rag_res = generate_chat_response(
            user_query=body.message,
            conversation_history=conversation_history,
            automation=matched_automation,
            use_local_ai=body.use_local_ai,
            ai_provider=body.ai_provider,
        )
        ai_response_text = rag_res["response"]
        sources = rag_res.get("sources", [])
        token_usage = rag_res.get("token_usage", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # If no results matched similarity threshold in the scoped workspace,
    # prompt the user to select and change the session workspace with metadata filtering
    # instead of returning an unhelpful dead-end message.
    if (not sources or ai_response_text == "I couldn't find relevant information in the knowledge base.") and matched_automation and matched_automation.lower() not in ("general", "all"):
        workspace_names = {
            "ROE": "Record of Employment (ROE)",
            "Overpayment": "Overpayment Support",
            "SyncPay": "SyncPay Support",
            "Monthly Hourly Update": "Monthly Hourly Update (MHU)",
            "Invoice Supplimental Details": "Invoice Supplemental Details (ISD)",
            "Infrastructure": "Infrastructure Support",
            "General": "General Support"
        }
        curr_name = workspace_names.get(matched_automation, matched_automation)
        prompt_content = f"[AUTOMATION_SELECT] I couldn't find relevant information within '{curr_name}'. Would you like to search in a different workspace, or select 'General Support' to search across all documentation?"
        ai_msg = crud.add_message(db, session_id, role="assistant", content=prompt_content)
        return ChatResponse(
            session_id=session_id,
            user_message=ChatMessageResponse.model_validate(user_msg),
            ai_message=ChatMessageResponse.model_validate(ai_msg),
            sources=[],
            token_usage=token_usage,
        )

    # Save the AI response with token metrics
    ai_msg = crud.add_message(
        db,
        session_id,
        role="assistant",
        content=ai_response_text,
        prompt_tokens=token_usage.get("prompt_tokens", 0),
        completion_tokens=token_usage.get("completion_tokens", 0),
        total_tokens=token_usage.get("total_tokens", 0),
        model_used=token_usage.get("model"),
        sources_json=json.dumps(sources) if sources else None,
    )


    # Auto-title the session on the first message
    if len(prior_messages) <= 1:
        auto_title = body.message[:50] + ("..." if len(body.message) > 50 else "")
        crud.update_session_title(db, session_id, auto_title)

    return ChatResponse(
        session_id=session_id,
        user_message=ChatMessageResponse.model_validate(user_msg),
        ai_message=ChatMessageResponse.model_validate(ai_msg),
        sources=sources,
        token_usage=token_usage,
    )


@router.post("/sessions/{session_id}/resume", response_model=ChatResponse)
def resume_session(
    session_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    If the session ended abruptly (e.g. page reload) after saving a user message
    but before the assistant could reply, this endpoint generates the missing response.
    """
    session = crud.get_session(db, session_id, user_id=x_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    prior_messages = crud.get_session_messages(db, session_id)
    if not prior_messages:
        raise HTTPException(status_code=400, detail="No messages found in session")

    # If the last message is already from assistant, we don't need to generate
    last_msg = prior_messages[-1]
    if last_msg.role == "assistant":
        # Return last user and assistant message pair
        user_msg = prior_messages[-2] if len(prior_messages) > 1 else last_msg
        return ChatResponse(
            session_id=session_id,
            user_message=ChatMessageResponse.model_validate(user_msg),
            ai_message=ChatMessageResponse.model_validate(last_msg),
        )

    if last_msg.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user to resume")

    # Infer automation type dynamically from message content or session
    matched_automation, _ = _detect_workspace(last_msg.content, session.automation)

    # If no keyword matches, we must show the select prompt
    if matched_automation is None:
        prompt_content = "[AUTOMATION_SELECT] Select which automation workspace this question is for:"
        ai_msg = crud.add_message(db, session_id, role="assistant", content=prompt_content)
        db.commit()
        return ChatResponse(
            session_id=session_id,
            user_message=ChatMessageResponse.model_validate(last_msg),
            ai_message=ChatMessageResponse.model_validate(ai_msg),
        )

    crud.update_session_automation(db, session_id, matched_automation)

    # Last message is from user. We need to generate the assistant reply!
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in prior_messages[:-1]
        if not msg.content.startswith("[AUTOMATION_SELECT")
    ]

    try:
        rag_res = generate_chat_response(
            user_query=last_msg.content,
            conversation_history=conversation_history,
            automation=matched_automation,
            use_local_ai=settings.USE_LOCAL_AI,
        )
        ai_response_text = rag_res["response"]
        sources = rag_res.get("sources", [])
        token_usage = rag_res.get("token_usage", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # Save the assistant response
    ai_msg = crud.add_message(
        db,
        session_id,
        role="assistant",
        content=ai_response_text,
        prompt_tokens=token_usage.get("prompt_tokens", 0),
        completion_tokens=token_usage.get("completion_tokens", 0),
        total_tokens=token_usage.get("total_tokens", 0),
        model_used=token_usage.get("model"),
        sources_json=json.dumps(sources) if sources else None,
    )

    return ChatResponse(
        session_id=session_id,
        user_message=ChatMessageResponse.model_validate(last_msg),
        ai_message=ChatMessageResponse.model_validate(ai_msg),
        sources=sources,
        token_usage=token_usage,
    )


class SelectionRequest(BaseModel):
    automation: str
    ai_provider: Optional[str] = None
    use_local_ai: Optional[bool] = None


@router.post("/sessions/{session_id}/select_automation", response_model=ChatResponse)
def select_session_automation(
    session_id: str,
    body: SelectionRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Deletes the selection prompt message, saves the selected automation workspace on the session,
    and processes the initial user query using the correct RAG filter.
    """
    session = crud.get_session(db, session_id, user_id=x_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save the chosen workspace onto the session record in DB
    crud.update_session_automation(db, session_id, body.automation)
    
    # Retrieve session messages
    messages = crud.get_session_messages(db, session_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages found to process")
        
    # The last message is the assistant's selection prompt.
    # The user's query is the message before it.
    user_msg = None
    prompt_msg = None
    for msg in reversed(messages):
        if msg.role == "assistant" and msg.content.startswith("[AUTOMATION_SELECT]"):
            prompt_msg = msg
        elif msg.role == "user" and (prompt_msg is not None or user_msg is None):
            user_msg = msg
            if prompt_msg is not None:
                break
            
    if not user_msg:
        raise HTTPException(status_code=400, detail="No user message found to answer")
        
    # Update the selection prompt message content to show the selection made
    if prompt_msg:
        workspace_names = {
            "ROE": "Record of Employment (ROE)",
            "Overpayment": "Overpayment Support",
            "SyncPay": "SyncPay Support",
            "Monthly Hourly Update": "Monthly Hourly Update (MHU)",
            "Invoice Supplimental Details": "Invoice Supplemental Details (ISD)",
            "Infrastructure": "Infrastructure Support",
            "General": "General Support"
        }
        selected_name = workspace_names.get(body.automation, body.automation)
        prompt_msg.content = f"[AUTOMATION_SELECTED] {selected_name}"

        
    # Get conversation history up to the user message
    prior_messages = [m for m in messages if m.id < user_msg.id]
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
        if not m.content.startswith("[AUTOMATION_SELECT")
    ]
    
    # Generate RAG response
    try:
        rag_res = generate_chat_response(
            user_query=user_msg.content,
            conversation_history=conversation_history,
            automation=body.automation,
            use_local_ai=body.use_local_ai,
            ai_provider=body.ai_provider,
        )
        ai_response_text = rag_res["response"]
        sources = rag_res.get("sources", [])
        token_usage = rag_res.get("token_usage", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

        
    # Save assistant response
    ai_msg = crud.add_message(
        db,
        session_id,
        role="assistant",
        content=ai_response_text,
        prompt_tokens=token_usage.get("prompt_tokens", 0),
        completion_tokens=token_usage.get("completion_tokens", 0),
        total_tokens=token_usage.get("total_tokens", 0),
        model_used=token_usage.get("model"),
        sources_json=json.dumps(sources) if sources else None,
    )
    
    # Update title based on the first query selection
    if len(messages) <= 2:
        session.title = f"{body.automation} Support" if body.automation != "General" else "General Support"
        
    db.commit()
    
    return ChatResponse(
        session_id=session_id,
        user_message=ChatMessageResponse.model_validate(user_msg),
        ai_message=ChatMessageResponse.model_validate(ai_msg),
        sources=sources,
        token_usage=token_usage,
    )

