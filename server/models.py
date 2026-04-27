from typing import Optional

from pydantic import BaseModel


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    text: str
    user_id: int
    chat_id: int
    forward_immediately: bool = True


class MessageEdit(BaseModel):
    """Schema for editing an existing message."""

    text: str


class MessageResponse(BaseModel):
    """Schema for message responses."""

    id: int
    user_id: int
    chat_id: int
    message_text: str
    edited_text: Optional[str] = None
    message_type: str
    forward_immediately: bool
    status: str
    sent_at: str
    forwarded_to_channels: Optional[str] = None
    created_at: str


class ForwardResponse(BaseModel):
    """Schema for forward operation response."""

    message_id: int
    status: str
    forwarded_to_channels: Optional[list[int]] = None
    error: Optional[str] = None
