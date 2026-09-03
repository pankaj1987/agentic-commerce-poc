from dotenv import load_dotenv
load_dotenv()
import os
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.observability import validate_langsmith
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.product_routes import router as product_router
from app.api.routes.cart_routes import router as cart_router
from app.api.routes.chat_routes import router as chat_router


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Runs once when FastAPI starts
    validate_langsmith()

    yield

    # Runs once when FastAPI shuts down
    # Add cleanup here later if required

app = FastAPI(
    title="Agentic Commerce API",
    description=(
        "AI-powered commerce API using "
        "LangChain, Shopify and RAG"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "UP",
        "service": "agentic-commerce-api",
    }


app.include_router(
    product_router,
    prefix="/api/products",
    tags=["Products"],
)

app.include_router(
    cart_router,
    prefix="/api/cart",
    tags=["Cart"],
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["AI Chat"],
)