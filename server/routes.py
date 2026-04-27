import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from server.models import (
    ForwardResponse,
    MessageCreate,
    MessageEdit,
    MessageResponse,
)
from services.database import (
    edit_message,
    forward_message,
    get_message_by_id,
    get_messages_with_filters,
    save_server_message,
    update_message_status,
)

router = APIRouter(prefix="/messages", tags=["messages"])

# Bot HTTP server URL (configurable via env for Docker)
BOT_HTTP_URL = os.getenv("BOT_HTTP_URL", "http://bot:8080")


def _to_response(msg: dict) -> MessageResponse:
    """Convert DB row to response model."""
    return MessageResponse(
        id=msg["id"],
        user_id=msg["user_id"],
        chat_id=msg["chat_id"],
        message_text=msg["message_text"],
        edited_text=msg.get("edited_text"),
        message_type=msg["message_type"],
        forward_immediately=bool(msg["forward_immediately"]),
        status=msg["status"],
        sent_at=msg["sent_at"],
        forwarded_to_channels=msg.get("forwarded_to_channels"),
        created_at=msg["created_at"],
    )


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(payload: MessageCreate) -> MessageResponse:
    """Create a new message.

    By default, messages are forwarded immediately via the bot.
    Set forward_immediately=False to queue for later manual forwarding.
    """
    message_id = save_server_message(
        text=payload.text,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        forward_immediately=payload.forward_immediately,
    )
    msg = get_message_by_id(message_id)
    if msg is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve message")

    # Forward immediately if requested
    if payload.forward_immediately and msg["status"] == "pending":
        formatted_text = _apply_wrappers(payload.text)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{BOT_HTTP_URL}/forward",
                    json={"message_id": message_id, "text": formatted_text},
                )
                if resp.status_code != 200:
                    update_message_status(message_id, "failed")
        except Exception:
            update_message_status(message_id, "failed")

    return _to_response(msg)


@router.get("", response_model=list[MessageResponse])
def list_messages(
    from_date: str = Query(None, description="Start date (ISO format)"),
    to_date: str = Query(None, description="End date (ISO format)"),
    status: str = Query(
        None, description="Filter by status (pending/forwarded/failed)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip N records"),
) -> list[MessageResponse]:
    """Retrieve messages with optional date and status filtering."""
    messages = get_messages_with_filters(
        from_date=from_date,
        to_date=to_date,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_to_response(msg) for msg in messages]


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: int) -> MessageResponse:
    """Get a specific message by ID."""
    msg = get_message_by_id(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return _to_response(msg)


@router.put("/{message_id}", response_model=MessageResponse)
def edit_message_route(message_id: int, payload: MessageEdit) -> MessageResponse:
    """Edit an existing message's text.

    Resets status to 'pending' so it can be re-forwarded.
    """
    if not edit_message(message_id, payload.text):
        raise HTTPException(status_code=404, detail="Message not found")
    msg = get_message_by_id(message_id)
    if msg is None:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve message after edit"
        )
    return _to_response(msg)


@router.post("/{message_id}/forward", response_model=ForwardResponse)
async def forward_message_route(
    message_id: int,
    channel_ids: list[int] = Query([], description="Target channel IDs"),
) -> ForwardResponse:
    """Manually trigger forwarding for a message.

    Use this when a message was created with forward_immediately=False.
    """
    msg = get_message_by_id(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")

    if msg["status"] == "forwarded":
        raise HTTPException(status_code=400, detail="Message already forwarded")

    if not channel_ids:
        raise HTTPException(
            status_code=400,
            detail="channel_ids query parameter is required",
        )

    try:
        result = forward_message(message_id, channel_ids)
        return ForwardResponse(**result)
    except Exception as e:
        update_message_status(message_id, "failed")
        return ForwardResponse(
            message_id=message_id,
            status="failed",
            error=str(e),
        )


def _apply_wrappers(text: str) -> str:
    """Apply wrapper prefix/suffix to message text."""
    from config import WRAPPER_PREFIX, WRAPPER_SUFFIX

    parts: list[str] = []
    if WRAPPER_PREFIX:
        parts.append(WRAPPER_PREFIX)
    parts.append(text)
    if WRAPPER_SUFFIX:
        parts.append(WRAPPER_SUFFIX)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts.append(f"⏰ {timestamp}")
    return "\n".join(parts)
