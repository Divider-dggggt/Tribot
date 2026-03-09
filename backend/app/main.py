from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/app_db")

app = FastAPI()

# Enable CORS for React frontend
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

@app.get("/")
def read_root():
    try:
        # Simple query to check DB connectivity
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
        return {"message": f"Users in DB: {count}"}
    except Exception as e:
        return {"message": f"Cannot connect to DB: {e}"}
