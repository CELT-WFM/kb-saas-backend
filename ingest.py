from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import boto3
import os
from db import get_db
from sqlalchemy.orm import Session
from models import Document
from pypdf import PdfReader
import pandas as pd
from docx import Document as DocxDocument

router = APIRouter()

# S3 setup
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    endpoint_url=os.getenv("S3_ENDPOINT")
)
BUCKET_NAME = os.getenv("S3_BUCKET")

def extract_text(file: UploadFile):
    ext = file.filename.split(".")[-1].lower()
    text = ""
    if ext == "pdf":
        reader = PdfReader(file.file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif ext in ["xls", "xlsx", "csv"]:
        df = pd.read_excel(file.file) if ext != "csv" else pd.read_csv(file.file)
        text = df.to_string()
    elif ext in ["docx", "doc"]:
        doc = DocxDocument(file.file)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return text

@router.post("/upload")
async def upload_file(
    collection_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(lambda: 1),  # For testing, replace with auth
    db: Session = Depends(get_db)
):
    try:
        # Save to S3
        s3_key = f"{user_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, BUCKET_NAME, s3_key)
        file.file.seek(0)  # reset file pointer

        # Extract text
        text_content = extract_text(file)

        # Save metadata to DB
        doc = Document(
            filename=file.filename,
            s3_key=s3_key,
            owner_id=user_id,
            collection_id=collection_id,
            file_type=file.filename.split(".")[-1].lower()
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        return {"success": True, "document_id": doc.id, "text_preview": text_content[:200]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

