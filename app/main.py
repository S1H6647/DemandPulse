from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import FastAPI

from app.api.routes import forecasts, health
from app.core.config import DATASET_DIR, MODEL_PATH
from app.runtime_assets import ensure_runtime_assets


# Load the dataset on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_assets(DATASET_DIR, MODEL_PATH)
    app.state.model = joblib.load(MODEL_PATH)

    app.state.datasets = {
        "train": pd.read_csv(DATASET_DIR / "train.csv", parse_dates=["date"]),
        "stores": pd.read_csv(DATASET_DIR / "stores.csv"),
        "transactions": pd.read_csv(
            DATASET_DIR / "transactions.csv", parse_dates=["date"]
        ),
        "holidays": pd.read_csv(
            DATASET_DIR / "holidays_events.csv", parse_dates=["date"]
        ),
        "oil": pd.read_csv(DATASET_DIR / "oil.csv", parse_dates=["date"]),
    }

    yield

    app.state.datasets.clear()
    del app.state.model


app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(forecasts.router)
