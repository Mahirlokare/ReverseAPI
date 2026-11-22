from fastapi import FastAPI
from apiscope.api.routes import router

app = FastAPI(title="APIScope", description="Hybrid API discovery and reverse-engineering platform (Week 1 foundation)", version="0.1.0")
app.include_router(router)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "apiscope", "version": "0.1.0"}
