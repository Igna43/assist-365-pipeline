from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    project: str
    api_base: str
    api_token: str
    bucket: str
    location: str
    raw_dataset: str = "raw"
    core_dataset: str = "core"
    mart_dataset: str = "mart"
    ops_dataset: str = "ops"

    @classmethod
    def from_env(cls, *, require_token: bool = True) -> Settings:
        load_dotenv()
        token = os.environ.get("A365_API_TOKEN", "")
        if require_token and not token:
            raise RuntimeError("A365_API_TOKEN is not set. Put it in .env or the environment.")
        return cls(
            project=os.environ.get("GCP_PROJECT", "a365-de-imangini"),
            api_base=os.environ.get(
                "A365_API_BASE",
                "https://h4zfbym5fd.execute-api.us-east-1.amazonaws.com/v1",
            ).rstrip("/"),
            api_token=token,
            bucket=os.environ.get("GCS_BUCKET", "a365-de-imangini-raw"),
            location=os.environ.get("BQ_LOCATION", "US"),
        )

    def table(self, dataset: str, name: str) -> str:
        return f"{self.project}.{dataset}.{name}"
