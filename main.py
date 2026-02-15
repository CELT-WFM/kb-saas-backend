from fastapi import FastAPI
from ingest import router as ingest_router
from db import Base, engine

app = FastAPI(title="KB SaaS V1")

# Create DB tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(ingest_router, prefix="/documents", tags=["Documents"])

@app.get("/health")
def health():
    return {"status": "ok"}

