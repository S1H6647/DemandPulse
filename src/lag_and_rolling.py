import pandas as pd

from src.history import add_history_features


def create_lag(df: pd.DataFrame, train: pd.DataFrame,
               arr: tuple[int, ...] = (1, 7, 14, 28)) -> pd.DataFrame:
    return add_history_features(
        df, train, ["store_nbr", "family"], "sales", arr, (), "lag_", "rolling_mean_"
    )


def create_rolling(df: pd.DataFrame, train: pd.DataFrame,
                   arr: tuple[int, ...] = (7, 14, 28)) -> pd.DataFrame:
    return add_history_features(
        df, train, ["store_nbr", "family"], "sales", (), arr, "lag_", "rolling_mean_"
    )


def create_lag_and_rolling(df: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    return add_history_features(
        df, train, ["store_nbr", "family"], "sales",
        (1, 7, 14, 28), (7, 14, 28), "lag_", "rolling_mean_"
    )
