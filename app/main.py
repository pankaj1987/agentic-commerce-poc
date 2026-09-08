# app/main.py

import logging

from contextlib import (
    asynccontextmanager,
)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)


# ============================================================
# ENVIRONMENT
# ============================================================
#
# Load environment variables before importing application
# components that depend on Settings.
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION IMPORTS
# ============================================================

from app.config.observability import (
    validate_langsmith,
)

from app.persistence.checkpointer import (
    close_checkpointer,
)

from app.api.routes.product_routes import (
    router as product_router,
)

from app.api.routes.cart_routes import (
    router as cart_router,
)

from app.api.routes.chat_routes import (
    router as chat_router,
)

from app.api.routes.order_routes import (
    router as order_router,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)


logger = logging.getLogger(
    __name__
)


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    # ========================================================
    # STARTUP
    # ========================================================

    logger.info(
        "Starting Agentic Commerce API."
    )

    validate_langsmith()

    logger.info(
        "Agentic Commerce API startup completed."
    )

    try:

        yield

    finally:

        # ====================================================
        # SHUTDOWN
        # ====================================================
        #
        # commerce_graph owns a long-lived PostgresSaver.
        #
        # close_checkpointer() closes the underlying Psycopg
        # connection cleanly when FastAPI shuts down.
        # ====================================================

        logger.info(
            "Shutting down Agentic Commerce API."
        )

        close_checkpointer()

        logger.info(
            "Agentic Commerce API shutdown completed."
        )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Agentic Commerce API",
    description=(
        "AI-powered commerce API using "
        "LangChain, LangGraph, Shopify and RAG"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

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


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/api/health"
)
def health_check():

    return {
        "status": "UP",
        "service": (
            "agentic-commerce-api"
        ),
    }


# ============================================================
# PRODUCT ROUTES
# ============================================================

app.include_router(
    product_router,
    prefix="/api/products",
    tags=[
        "Products"
    ],
)


# ============================================================
# CART ROUTES
# ============================================================

app.include_router(
    cart_router,
    prefix="/api/cart",
    tags=[
        "Cart"
    ],
)


# ============================================================
# ORDER ROUTES
# ============================================================

app.include_router(
    order_router,
    prefix="/api/orders",
    tags=[
        "Orders"
    ],
)


# ============================================================
# AI CHAT ROUTES
# ============================================================
#
# chat_routes.py should define:
#
# router = APIRouter(
#     prefix="/chat",
#     ...
# )
#
# Combined route:
#
# /api + /chat
# =
# POST /api/chat
#
# ============================================================

app.include_router(
    chat_router,
    prefix="/api",
    tags=[
        "AI Chat"
    ],
)