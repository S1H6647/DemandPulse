"""Download immutable model/data assets from Hugging Face when configured."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ASSET_FILES = (
    "train.csv",
    "stores.csv",
    "transactions.csv",
    "holidays_events.csv",
    "oil.csv",
)


def _download(
    repo_id: str, revision: str, remote_name: str, destination: Path, token: str | None
) -> None:
    url = (
        f"https://huggingface.co/datasets/{quote(repo_id, safe='/')}"
        f"/resolve/{quote(revision, safe='')}/{quote(remote_name, safe='/')}?download=true"
    )
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.download")
    try:
        with (
            urllib.request.urlopen(request, timeout=300) as response,
            temporary.open("wb") as output,
        ):
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary.replace(destination)
    except (urllib.error.URLError, OSError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"Could not download {remote_name!r} from Hugging Face repository {repo_id!r}."
        ) from exc


def ensure_runtime_assets(dataset_dir: Path, model_path: Path) -> None:
    """Download assets when ``HF_DATASET_REPO`` is set.

    The repository is public by default for this project. Set ``HF_TOKEN`` on
    Render only when the Hugging Face dataset is private. Existing local files
    are reused, which keeps local development and tests offline.
    """

    repo_id = os.getenv("HF_DATASET_REPO", "S1H6647/demandpulse").strip()
    revision = os.getenv("HF_DATASET_REVISION", "main").strip()
    token = os.getenv("HF_TOKEN")
    remote_prefix = os.getenv("HF_DATASET_PREFIX", "").strip("/")
    remote_model = os.getenv("HF_MODEL_FILE", "xgb_best_v2.joblib").strip("/")

    for filename in ASSET_FILES:
        destination = dataset_dir / filename
        if not destination.exists():
            remote_name = f"{remote_prefix}/{filename}" if remote_prefix else filename
            _download(repo_id, revision, remote_name, destination, token)

    if not model_path.exists():
        remote_name = (
            f"{remote_prefix}/{remote_model}" if remote_prefix else remote_model
        )
        _download(repo_id, revision, remote_name, model_path, token)
