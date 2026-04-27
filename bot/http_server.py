from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot.bot import bot
from config import CHANNEL_IDS
from services.database import forward_message, update_message_status

app = FastAPI(title="Bot HTTP Server")


class ForwardRequest(BaseModel):
    """Request to forward a message to channels."""

    message_id: int
    text: str


@app.post("/forward")
def forward_message_endpoint(payload: ForwardRequest) -> dict:
    """Receive a message from the API server and forward it to channels.

    The API server calls this when forward_immediately=true.
    """
    try:
        results = []
        for channel_id in CHANNEL_IDS:
            result = bot.send_message(
                chat_id=channel_id,
                text=payload.text,
            )
            results.append(result.message_id)
        forward_message(payload.message_id, CHANNEL_IDS)
        return {
            "status": "forwarded",
            "message_id": payload.message_id,
            "telegram_message_ids": results,
        }
    except Exception as e:
        update_message_status(payload.message_id, "failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}
