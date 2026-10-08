"""Cấu hình dùng chung cho toàn bộ ứng dụng.

File này chỉ chịu trách nhiệm đọc biến môi trường. Việc gom cấu hình vào một
nơi giúp các service không phải tự đọc ``.env`` nhiều lần và tránh ghi API key
trực tiếp trong source code.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


# Nạp các biến trong file .env (nếu có) vào môi trường của tiến trình Python.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Đại diện cho toàn bộ cấu hình cần thiết của chatbot."""

    pinecone_api_key: str
    pinecone_index_name: str
    pinecone_namespace: str
    openai_api_key: str
    openai_base_url: str | None
    openai_model: str
    openai_timeout: float
    frontend_origin: str
    top_k: int


def _required_env(name: str) -> str:
    """Đọc một biến môi trường bắt buộc và báo lỗi rõ ràng nếu bị thiếu."""

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Thiếu biến môi trường bắt buộc: {name}")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Tạo và cache cấu hình để toàn ứng dụng dùng chung một đối tượng.

    ``lru_cache`` giúp hàm chỉ thực sự đọc và kiểm tra môi trường một lần trong
    vòng đời của tiến trình FastAPI.
    """

    return Settings(
        pinecone_api_key=_required_env("PINECONE_API_KEY"),
        pinecone_index_name=os.getenv(
            "PINECONE_INDEX_NAME", "recruitment-chatbot"
        ),
        pinecone_namespace=os.getenv(
            "PINECONE_NAMESPACE", "company-demo"
        ),
        openai_api_key=_required_env("OPENAI_API_KEY"),
        # Để trống để dùng endpoint mặc định của OpenAI.
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip() or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_timeout=float(os.getenv("OPENAI_TIMEOUT", "60")),
        frontend_origin=os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:5173"
        ),
        top_k=int(os.getenv("RAG_TOP_K", "5")),
    )
