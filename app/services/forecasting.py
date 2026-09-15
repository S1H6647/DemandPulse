import pandas as pd

from app.schemas.forecast import ForecastRequest
from src.features import build_features


def predict_forecast(payload: ForecastRequest, model, datasets) -> float:
    features = build_forecast_features(payload, datasets)
    return max(0.0, round(float(model.predict(features)[0]), 2))


def build_forecast_features(payload: ForecastRequest, datasets):
    date = pd.Timestamp(payload.date)
    start = date - pd.Timedelta(days=28)
    train = datasets["train"]
    transactions = datasets["transactions"]
    history = {
        **datasets,
        "train": train.loc[
            (train["store_nbr"] == payload.store_nbr)
            & (train["family"] == payload.family)
            & train["date"].between(start, date, inclusive="left")
        ],
        "transactions": transactions.loc[
            (transactions["store_nbr"] == payload.store_nbr)
            & transactions["date"].between(start, date, inclusive="left")
        ],
    }
    return build_features(pd.DataFrame([payload.model_dump()]), history)
