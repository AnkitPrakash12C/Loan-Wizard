# """
# backend/config.py
# Centralized settings loaded from .env
# """
# from pydantic_settings import BaseSettings
# from functools import lru_cache
#
#
# class Settings(BaseSettings):
#     # App
#     app_secret_key: str = "change-me"
#     app_env: str = "development"
#     base_url: str = "http://localhost:8000"
#
#     # Database
#     database_url: str = "sqlite+aiosqlite:///./loan_wizard.db"
#
#     # LLM
#     # anthropic_api_key: str = ""
#     # llm_model: str = "claude-opus-4-5"
#     gemini_api_key: str = ""
#     llm_model: str = "gemini-1.5-flash"
#
#     # STT
#     stt_provider: str = "whisper"
#     deepgram_api_key: str = ""
#
#     # JWT
#     jwt_algorithm: str = "HS256"
#     jwt_expire_minutes: int = 60
#
#     # AWS (optional)
#     aws_access_key_id: str = ""
#     aws_secret_access_key: str = ""
#     s3_bucket: str = ""
#     s3_region: str = "ap-south-1"
#
#     class Config:
#         env_file = ".env"
#         case_sensitive = False
#
#
# @lru_cache()
# def get_settings() -> Settings:
#     return Settings()

"""
backend/config.py
Centralized settings loaded from .env
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_secret_key: str = "change-me"
    app_env: str = "development"
    base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./loan_wizard.db"

    # LLM - Gemini
    gemini_api_key: str = ""
    llm_model: str = "gemini-1.5-flash"

    # STT
    stt_provider: str = "whisper"
    deepgram_api_key: str = ""

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # AWS (optional)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_region: str = "ap-south-1"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()