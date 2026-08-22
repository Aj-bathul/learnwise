import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    DB_USER = os.environ.get("DB_USER", "learnwise_app")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "learnwise")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # Path to the trained ML model artifact (built in Phase 6)
    ML_MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ml", "difficulty_model.joblib"
    )
