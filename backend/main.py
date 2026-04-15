from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.version import get_project_version
from app.models import ChatMessage, ChatSession  # noqa: F401
from app.routers.chat import router as chat_router
from app.routers.persona import router as persona_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tokendancer Persona Station API",
        version=get_project_version(),
        docs_url="/persona-api/docs",
        openapi_url="/persona-api/openapi.json",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(persona_router)
    app.include_router(chat_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)
