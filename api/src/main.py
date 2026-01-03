from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import engine, SessionLocal, Base
from src.seed import seed_portfolios
from src.routers import portfolios, risk, stress


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_portfolios(db)
    yield


app = FastAPI(title="CerberusRisk API", lifespan=lifespan)

app.include_router(portfolios.router)
app.include_router(risk.router)
app.include_router(stress.router)


@app.get("/health")
def health():
    return {"status": "ok"}
