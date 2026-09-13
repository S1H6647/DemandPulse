# DemandPulse

DemandPulse forecasts daily sales for a store and product family using historical
sales, transactions, promotions, store information, holidays, and oil prices.
It combines a model-training notebook with a FastAPI service that serves an
XGBoost pipeline. Training and inference share the same feature builder.

## Date handling

**History features use exact prior calendar dates and exclude the forecast date.**
This prevents current-day and future observations from leaking into predictions.

### Parsing dates and extracting calendar features

Send API dates as `YYYY-MM-DD`. Pydantic validates the field as a Python `date`,
CSV date columns are parsed with pandas, and feature construction converts request
dates to pandas datetimes. The project operates at daily resolution; it does not
implement timezone conversion or intraday forecasting.

The requested date produces these model inputs:

| Feature | Meaning |
| --- | --- |
| `year` | Calendar year |
| `month` | Month from 1 to 12 |
| `day_of_week` | Monday = 0 through Sunday = 6 |
| `is_weekend` | 1 for Saturday/Sunday, otherwise 0 |

After history lookups and calendar joins, the raw `date` column is removed.
The row ID and target `sales` are also excluded from model inputs.

### Calendar-day lags and rolling averages

For forecast date `D`, the API selects history in **`[D − 28 days, D)`**: the
lower boundary is included and the forecast day is excluded.

| History | Grouping | Lag days | Rolling windows |
| --- | --- | --- | --- |
| Sales | Store and product family | 1, 7, 14, 28 | 7, 14, 28 days |
| Transactions | Store | 1, 7, 14, 28 | 7, 14, 28 days |

A lag of `n` looks up exactly `D − n days`, rather than shifting by row position.
A rolling mean of `n` averages the observations from `D − n days` through
`D − 1 day`, inclusive. Sales features are named `lag_1`, `lag_7`, and so on,
and `rolling_mean_7`, `rolling_mean_14`, and `rolling_mean_28`. Transaction
features use the prefixes `transactions_lag_` and `transactions_rolling_`.

For a forecast on **2017-08-16**:

- `lag_1` uses sales on **2017-08-15**.
- `lag_7` uses sales on **2017-08-09**.
- `rolling_mean_7` averages **2017-08-09 through 2017-08-15**.
- The full history slice covers **2017-07-19 through 2017-08-15**.

If August 15 is missing, `lag_1` remains missing; August 14 does not become
"yesterday." Rolling means require a complete daily window, so a missing day
makes that rolling feature missing too. The model preprocessor replaces missing
numeric features with `-1`, not zero sales. Duplicate group/date history keys
raise an error because each key must identify one observation.

See [src/history.py](src/history.py) for the exact-date lookups,
[src/features.py](src/features.py) for the shared feature pipeline, and
[app/services/forecasting.py](app/services/forecasting.py) for API history filtering.

### Oil prices, holidays, and promotions

Oil uses the latest non-missing observation **strictly before** the requested date
through a backward as-of join. Same-day and future oil values are excluded. If no
earlier value exists, the feature remains missing until preprocessing.

Holidays match the requested date and store location. National events apply to
all stores, regional events match the store's state, and local events match its
city. Multiple event types are combined; `transferred` is retained as a feature.
The feature builder does not move events to another date itself. Unmatched dates
receive `No Holiday`.

The request supplies `onpromotion` for the forecast date. Promotions and holiday
calendars are assumed known when forecasting.

### Chronological splits and forecast limits

V2 reserves the final 28 calendar days for testing and the preceding 28 days for
validation. Training uses only earlier dates. Boundaries are derived from the
maximum date in `train.csv`; the saved evaluation record uses:

| Split | Dates |
| --- | --- |
| Training | Before 2017-06-21 |
| Validation | 2017-06-21 through 2017-07-18 |
| Test | 2017-07-19 through 2017-08-15 |

Evaluation is **rolling one-day-ahead**: each prediction can use previous days'
observed sales and transactions, including earlier days within the holdout period.
The model is fitted only on training-period labels.

These scores do not establish accuracy for forecasting a whole future period
from one fixed starting date. The API does not recursively generate future sales
or transactions. Dates beyond available history can have missing lag and rolling
features, and the API does not reject dates solely because history is incomplete.
Historical requests may overlap training and are not held-out accuracy estimates.

## Setup

Use Python 3.12 or later; `.python-version` selects 3.12. From the project root:

```sh
uv sync
uv pip install --python .venv/bin/python -r requirements-notebooks.txt
```

`pyproject.toml` declares API dependencies. `requirements-notebooks.txt` includes
the machine-learning packages in `requirements.txt`, plus notebook and plotting
tools. The API also needs the machine-learning packages to load the saved model.

Place these CSV files in `datasets/`:

| File | Required columns |
| --- | --- |
| `train.csv` | `id`, `date`, `store_nbr`, `family`, `sales`, `onpromotion` |
| `stores.csv` | `store_nbr`, `city`, `state`, `type`, `cluster` |
| `transactions.csv` | `date`, `store_nbr`, `transactions` |
| `holidays_events.csv` | `date`, `type`, `locale`, `locale_name`, `transferred` |
| `oil.csv` | `date`, `dcoilwtico` |

Datasets and generated model artifacts are ignored by Git and must be supplied
locally. The API does not load `test.csv` or `sample_submission.csv`.

## Train V2

Open [notebooks/V2.ipynb](notebooks/V2.ipynb) with the project's `.venv` Python
environment and run all cells. The notebook fits linear regression, random forest, XGBoost, and
15 XGBoost search candidates. It saves the selected XGBoost pipeline to
`artifacts/V2_models/xgb_best_v2.joblib`, along with a metrics JSON record.
An existing model is backed up before replacement if the backup does not already
exist. The metrics record includes split dates, package versions, parameters, and
source/code hashes. The notebook also saves `artifacts/v2_test_mae.png`.

Training defaults to a seeded sample of 300,000 rows and two CPU threads to limit
memory and CPU usage. Set `MAX_TRAIN_ROWS = None` in V2 to use all eligible training
rows. Validation and test each use every row from a separate 28-day period at the
end of the dataset. The selected model is fitted only on training-period labels.

History lookups still use the full source history when training targets are
sampled. Model selection compares tuned and untuned XGBoost by validation MAE.

## Run the API

### Next.js frontend

The web interface lives in [frontend/](frontend/README.md). Start the API below,
then run these commands in a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 for the forecast form, live predictions, and calendar
history panel. Next.js forwards requests to FastAPI at `http://127.0.0.1:8000`;
set `BACKEND_URL` in `frontend/.env.local` to change that address.

### Backend server

```sh
.venv/bin/uvicorn app.main:app --reload
```

The datasets and saved model must exist before startup. Restart the server after
updating either: both are loaded at startup. `DATASET_DIR` and `MODEL_PATH` override
the defaults `datasets/` and `artifacts/V2_models/xgb_best_v2.joblib`.

Interactive API documentation is at `http://127.0.0.1:8000/docs`.
`GET /health` returns a server status message.

```json
{
  "date": "2016-08-14",
  "store_nbr": 54,
  "family": "GROCERY I",
  "onpromotion": 42
}
```

Send this JSON to `POST /forecast`, for example:

```sh
curl -X POST http://127.0.0.1:8000/forecast \
  -H 'Content-Type: application/json' \
  -d '{"date":"2016-08-14","store_nbr":54,"family":"GROCERY I","onpromotion":42}'
```

`store_nbr` must be positive, `family` nonempty, and `onpromotion` a nonnegative
integer. Use store IDs and family names from your datasets. The response includes
`date`, `store_nbr`, `family`, and `predicted_sales`. Predictions are nonnegative
and rounded to two decimal places.

## Project layout

```text
app/                    FastAPI application, schemas, and forecast service
src/features.py         Shared training and inference feature builder
src/history.py          Calendar-day history lookups
src/lag_and_rolling.py   Sales lag and rolling feature definitions
src/preprocessor.py     Missing-value handling and categorical encoding
notebooks/V2.ipynb       Training, evaluation, and model export
datasets/               Local CSV inputs (Git-ignored)
artifacts/              Local models and evaluation outputs (Git-ignored)
```

V1 and `training_data_v1.joblib` are legacy experiments. Use V2 for the shared
calendar-based features and chronological splits. V2 checks unique history keys,
required sales values, and nonnegative sales/promotions before fitting.

## Verify date handling

If the local `tests/` directory is available, run:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The existing tests cover grouped calendar-day history, missing and duplicate
observations, matching batch/API features, row-order preservation, and exclusion
of same-day/future sales and oil values. `tests/` is currently ignored by Git and
may be absent from a fresh checkout. V2 also checks training/API feature parity
before fitting models.
