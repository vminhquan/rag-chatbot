"""Các thao tác đọc/ghi dữ liệu với Pinecone.

Index của dự án dùng integrated embedding. Ứng dụng gửi văn bản ở trường
``text`` và Pinecone tự embedding bằng llama-text-embed-v2.
"""

from functools import lru_cache
from typing import Any

from pinecone import Pinecone

from app.config import get_settings
from app.schema import SourceDocument


@lru_cache(maxsize=1)
def get_pinecone_client() -> Pinecone:
    """Khởi tạo một Pinecone client dùng chung cho toàn tiến trình."""

    settings = get_settings()
    return Pinecone(api_key=settings.pinecone_api_key)


@lru_cache(maxsize=1)
def get_index():
    """Trả về kết nối tới index đã được scripts/create_index.py tạo."""

    settings = get_settings()
    return get_pinecone_client().Index(settings.pinecone_index_name)


def _read_value(value: Any, key: str, default: Any = None) -> Any:
    """Đọc dữ liệu từ cả dict lẫn object do các phiên bản SDK trả về."""

    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def search_documents(
    question: str,
    namespace: str,
    top_k: int,
    filters: dict | None = None,
) -> list[SourceDocument]:
    """Tìm các đoạn tài liệu có ý nghĩa gần nhất với câu hỏi.

    Pinecone tự chuyển ``question`` thành vector truy vấn bằng model embedding
    gắn với index. Kết quả được chuẩn hóa thành SourceDocument để tầng RAG
    không phụ thuộc vào cấu trúc response cụ thể của Pinecone SDK.
    """

    query_payload: dict = {
        "top_k": top_k,
        "inputs": {"text": question},
    }
    if filters:
        query_payload["filter"] = filters

    result = get_index().search(
        namespace=namespace,
        query=query_payload,
    )

    result_body = _read_value(result, "result", {})
    hits = _read_value(result_body, "hits", []) or []
    documents: list[SourceDocument] = []

    for hit in hits:
        fields = _read_value(hit, "fields", {}) or {}
        content = _read_value(fields, "text", "")
        if not content:
            continue

        documents.append(
            SourceDocument(
                id=str(
                    _read_value(hit, "_id", _read_value(hit, "id", ""))
                ),
                content=str(content),
                source=str(_read_value(fields, "source", "Không rõ nguồn")),
                # SDK hiện tại dùng ``score``; một số response JSON dùng
                # ``_score`` nên hỗ trợ cả hai dạng.
                score=float(
                    _read_value(hit, "_score", _read_value(hit, "score", 0.0))
                ),
                company_id=_read_value(fields, "company_id"),
                company_name=_read_value(fields, "company_name"),
                job_title=_read_value(fields, "job_title"),
                industry=_read_value(fields, "industry"),
                location=_read_value(fields, "location"),
                status=_read_value(fields, "status"),
            )
        )

    return documents


def upsert_documents(records: list[dict], namespace: str) -> None:
    """Gửi một batch tài liệu text vào Pinecone để embedding và lưu trữ."""

    if records:
        get_index().upsert_records(namespace=namespace, records=records)
