from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.version import get_project_version
from app.core.schema_upgrade import upgrade_runtime_schema
from app.models import ChatMessage, ChatSession, CreatedPersona, LLMConfig  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.persona_admin import router as persona_admin_router
from app.routers.chat import router as chat_router
from app.routers.persona import router as persona_router
from app.routers.how_to_do import router as how_to_do_router
from app.routers.reply_assistant import router as reply_assistant_router
from app.routers.image_lab import router as image_lab_router


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
        upgrade_runtime_schema(engine)

    app.include_router(persona_router)
    app.include_router(auth_router, prefix="/persona-api")
    app.include_router(persona_admin_router)
    app.include_router(chat_router)
    app.include_router(how_to_do_router)
    app.include_router(reply_assistant_router)
    app.include_router(image_lab_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)
