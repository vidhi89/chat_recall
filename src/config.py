import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "ChatRecall")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    DATA_DIR: str = "data"
    RAW_DATA_DIR: str = "data/raw"
    EVALUATION_DIR: str = "data/evaluation"
    EMBEDDINGS_DIR: str = "data/embeddings"


settings = Settings()