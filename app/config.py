import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/aharya.db"
    upload_dir: Path = Path("./data/uploads")
    max_upload_mb: int = 15

    # "auto" uses Claude when an API key is available, else the offline path.
    llm_mode: Literal["auto", "claude", "offline"] = "auto"
    anthropic_api_key: str | None = None
    extraction_model: str = "claude-opus-5-5"
    planner_model: str = "claude-opus-5-5"

    # Reports older than this are flagged as stale.
    stale_report_days: int = 90

    @property
    def use_llm(self) -> bool:
        if self.llm_mode == "auto":
            return bool(self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))
        return self.llm_mode == "claude"


settings = Settings()
