from fastapi import APIRouter, Request

from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecasting import predict_forecast

router = APIRouter(
    prefix="/forecast",
    tags=["forecast"],
)


@router.get("/options")
async def get_forecast_options(request: Request):
    """Dataset-backed choices and date bounds for the forecast form."""
    datasets = request.app.state.datasets
    train = datasets["train"]
    stores = datasets["stores"].sort_values("store_nbr")
    return {
        "stores": [
            {"store_nbr": int(row.store_nbr), "city": str(row.city)}
            for row in stores.itertuples()
        ],
        "families": sorted(train["family"].dropna().unique().tolist()),
        "history_start": train["date"].min().date().isoformat(),
        "history_end": train["date"].max().date().isoformat(),
    }


@router.post("", response_model=ForecastResponse)
async def get_forecast(payload: ForecastRequest, request: Request):

    prediction: float = predict_forecast(
        payload, model=request.app.state.model, datasets=request.app.state.datasets
    )

    return ForecastResponse(
        date=payload.date,
        store_nbr=payload.store_nbr,
        family=payload.family,
        predicted_sales=float(prediction),
    )
