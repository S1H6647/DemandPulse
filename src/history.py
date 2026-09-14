"""Calendar-day history shared by notebook training and API requests."""

import numpy as np
import pandas as pd


def add_history_features(df, history, keys, value, lags, windows, lag_prefix, rolling_prefix):
    df = df.copy()
    
    df["date"] = pd.to_datetime(df["date"])
    history = history[[*keys, "date", value]].copy()
    history["date"] = pd.to_datetime(history["date"])
    index_columns = [*keys, "date"]
    values = history.set_index(index_columns)[value]
    if not values.index.is_unique:
        raise ValueError(f"Duplicate history rows for {index_columns}")
    if any(n <= 0 for n in (*lags, *windows)):
        raise ValueError("History windows must be positive")

    # Look up exact dates, so a missing day never becomes the previous day.
    lookup = df[index_columns].copy()
    total = np.zeros(len(df))
    for days in range(1, max((*lags, *windows), default=0) + 1):
        lookup["date"] = df["date"] - pd.Timedelta(days=days)
        past = values.reindex(pd.MultiIndex.from_frame(lookup)).to_numpy(dtype=float)
        total += past
        if days in lags:
            df[f"{lag_prefix}{days}"] = past.astype("float32")
        if days in windows:
            # Missing daily observations propagate to the complete window.
            df[f"{rolling_prefix}{days}"] = (total / days).astype("float32")
    return df
