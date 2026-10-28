from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    header_footer_threshold: float = 0.4  # line repeated on >=40% of pages = header/footer
    min_page_chars: int = 30


settings = Settings()
