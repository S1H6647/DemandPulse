import pandas as pd

from app.core.config import DATASET_DIR
from src.history import add_history_features


def create_transactions_lag(df: pd.DataFrame,
                            arr: tuple[int, ...] = (1, 7, 14, 28),
                            history: pd.DataFrame | None = None) -> pd.DataFrame:
    if history is None:
        history = pd.read_csv(DATASET_DIR / "transactions.csv", parse_dates=["date"])
    return add_history_features(
        df, history, ["store_nbr"], "transactions", arr, (),
        "transactions_lag_", "transactions_rolling_"
    )


def create_transactions_rolling(df: pd.DataFrame,
                                arr: tuple[int, ...] = (7, 14, 28),
                                history: pd.DataFrame | None = None) -> pd.DataFrame:
    if history is None:
        history = pd.read_csv(DATASET_DIR / "transactions.csv", parse_dates=["date"])
    return add_history_features(
        df, history, ["store_nbr"], "transactions", (), arr,
        "transactions_lag_", "transactions_rolling_"
    )
