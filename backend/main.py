from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.persona import router as persona_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Tokendancer Persona Station API",
        version="V1.0.0",
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

    app.include_router(persona_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)
