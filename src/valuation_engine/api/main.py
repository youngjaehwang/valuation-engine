from fastapi import FastAPI
import uvicorn

from valuation_engine.api.routers.spotrate import router as spotrate_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="valuation-engine",
        version="0.1.0",
        description="Fair Value & Valuation Engine API",
    )
    app.include_router(spotrate_router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "valuation_engine.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
