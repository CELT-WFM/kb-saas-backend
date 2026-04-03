import os
import json
import stripe
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Local imports
from db import Base, engine, get_db
from models import User, Collection, Chunk
from auth import verify_token, hash_password, verify_password, create_access_token
from ingest import router as ingest_router

# Initialize Application
app = FastAPI(title="KB SaaS V1")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database Setup
Base.metadata.create_all(bind=engine)

# Stripe Config
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Include Routers
app.include_router(ingest_router, prefix="/documents", tags=["Documents"])

# --- Pydantic Schemas ---
class AuthBody(BaseModel):
    email: str
    password: str

class SearchBody(BaseModel):
    query: str
    collection_id: int
    top_k: int = 5

# --- Routes ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register")
def register(body: AuthBody, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=body.email, 
        hashed_password=hash_password(body.password)
    )
    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login(body: AuthBody, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"access_token": create_access_token({"user_id": user.id})}

@app.post("/collections")
def create_collection(
    body: dict, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    c = Collection(name=body["name"], owner_id=user_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}

@app.post("/search")
def search(
    body: SearchBody, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    # Note: This is currently a simple filter. 
    # You'll likely want to implement vector search here later using pgvector.
    chunks = db.query(Chunk).filter_by(collection_id=body.collection_id).all()
    results = [
        {"content": c.content, "source": getattr(c, 'source_url', None)} 
        for c in chunks[:body.top_k]
    ]
    return {"results": results}

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "customer.subscription.deleted":
        customer_id = event["data"]["object"]["customer"]
        user = db.query(User).filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.is_active = False
            db.commit()
            
    return {"received": True}
