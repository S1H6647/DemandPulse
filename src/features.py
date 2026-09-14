"""The same feature builder is used for training and serving."""

import pandas as pd

from src.history import add_history_features
from src.lag_and_rolling import create_lag_and_rolling


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["id", "sales"], errors="ignore").copy()
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.day_of_week
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    return df


def build_features(rows: pd.DataFrame, datasets: dict) -> pd.DataFrame:
    df = clean_features(rows)
    df["_row_order"] = range(len(df))
    df = create_lag_and_rolling(df, datasets["train"])
    df = add_history_features(
        df, datasets["transactions"], ["store_nbr"], "transactions",
        (1, 7, 14, 28), (7, 14, 28), "transactions_lag_", "transactions_rolling_"
    )
    stores = datasets["stores"]
    df = df.merge(stores, on="store_nbr", how="left", validate="many_to_one")

    # Yesterday's most recently available oil price is known at forecast time.
    oil = datasets["oil"].sort_values("date")
    oil = oil.dropna(subset=["dcoilwtico"])
    oil["date"] = pd.to_datetime(oil["date"]).astype("datetime64[ns]")
    df = pd.merge_asof(
        df.sort_values("date"), oil, on="date", direction="backward",
        allow_exact_matches=False,
    )
    df = df.rename(columns={"dcoilwtico": "oil_price_previous"})

    holidays = datasets["holidays"].rename(columns={"type": "holiday_type"})
    events = holidays.merge(stores[["store_nbr", "city", "state"]], how="cross")
    applies = (
        events["locale"].eq("National")
        | (events["locale"].eq("Regional") & events["locale_name"].eq(events["state"]))
        | (events["locale"].eq("Local") & events["locale_name"].eq(events["city"]))
    )
    calendar = events.loc[applies].groupby(["date", "store_nbr"], as_index=False).agg(
        holiday_type=("holiday_type", lambda s: " | ".join(sorted(s.dropna().unique()))),
        transferred=("transferred", "any"),
    )
    df = df.merge(calendar, on=["date", "store_nbr"], how="left", validate="many_to_one")
    df["holiday_type"] = df["holiday_type"].fillna("No Holiday")
    df["transferred"] = df["transferred"].astype("boolean").fillna(False).astype(int)
    df = df.sort_values("_row_order").drop(columns="_row_order")
    df.index = rows.index

    # Explicit types keep stores/categories identical in training and serving.
    for column in ["store_nbr", "family", "city", "state", "type", "cluster", "holiday_type"]:
        df[column] = df[column].astype(str)
    for column in df.select_dtypes(include="number"):
        df[column] = df[column].astype("float32")
    return df.drop(columns="date")
