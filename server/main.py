from fastapi import FastAPI

from server.routes import router

app = FastAPI(
    title="Telegram Job Notifier API",
    description="API for managing and forwarding messages to Telegram channels",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
