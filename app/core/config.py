import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = Path(os.getenv("DATASET_DIR", str(PROJECT_ROOT / "datasets")))

MODEL_PATH = Path(
    os.getenv(
        "MODEL_PATH", str(PROJECT_ROOT / "artifacts/V2_models/xgb_best_v2.joblib")
    )
)
