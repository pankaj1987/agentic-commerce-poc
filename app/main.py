import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load configuration first.
load_dotenv()

# Configure logging before imports that construct LangGraph/checkpointer objects.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

from app.security.redaction import install_sensitive_data_filter
install_sensitive_data_filter()

from app.config.observability import validate_langsmith
from app.persistence.checkpointer import close_checkpointer
from app.api.routes.product_routes import router as product_router
from app.api.routes.cart_routes import router as cart_router
from app.api.routes.chat_routes import router as chat_router
from app.api.routes.order_routes import router as order_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agentic Commerce API.")
    validate_langsmith()
    logger.info("Agentic Commerce API startup completed.")
    try:
        yield
    finally:
        logger.info("Shutting down Agentic Commerce API.")
        close_checkpointer()
        logger.info("Agentic Commerce API shutdown completed.")


app = FastAPI(
    title="Agentic Commerce API",
    description="AI-powered commerce API using LangChain, LangGraph, Shopify and RAG",
    version="1.0.0-phase5a",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "UP", "service": "agentic-commerce-api"}


app.include_router(product_router, prefix="/api/products", tags=["Products"])
app.include_router(cart_router, prefix="/api/cart", tags=["Cart"])
app.include_router(order_router, prefix="/api/orders", tags=["Orders"])
app.include_router(chat_router, prefix="/api", tags=["AI Chat"])
