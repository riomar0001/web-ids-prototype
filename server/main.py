"""
FastAPI application factory.

Creates the app, loads ML models, registers the IDS middleware,
and includes route modules.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.middleware.ids import IDSMiddleware
from server.routes.health import router as health_router
from server.services.classifier import IDSClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Web IDS Middleware",
        description="Intrusion Detection System middleware using Random Forest classification",
        version="0.1.0",
    )

    # Load models once at startup
    classifier = IDSClassifier()

    # CORS — allow the React dashboard to fetch logs
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register the global IDS middleware
    application.add_middleware(IDSMiddleware, classifier=classifier)

    # Register routes
    application.include_router(health_router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
