"""Đọc catalog công ty công khai dùng cho API và kiểm tra namespace."""

import json
from functools import lru_cache
from pathlib import Path


CATALOG_FILE = Path(__file__).resolve().parents[1] / "data" / "companies.json"
PUBLIC_NAMESPACE = "public-jobs"


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """Đọc catalog một lần và cache trong vòng đời của FastAPI."""

    if not CATALOG_FILE.exists():
        raise RuntimeError(f"Không tìm thấy catalog: {CATALOG_FILE}")
    return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))


def get_companies() -> list[dict]:
    """Trả danh sách công ty gọn nhẹ để frontend dựng bộ chọn."""

    return [
        {
            "id": company["id"],
            "name": company["name"],
            "industry": company["industry"],
            "location": company["location"],
        }
        for company in load_catalog()["companies"]
    ]


def get_company_ids() -> set[str]:
    """Tạo allow-list company_id; không tin namespace do trình duyệt tự gửi."""

    return {company["id"] for company in load_catalog()["companies"]}


def get_company(company_id: str) -> dict | None:
    """Tìm đầy đủ dữ liệu một công ty theo ID trong catalog."""

    return next(
        (
            company
            for company in load_catalog()["companies"]
            if company["id"] == company_id
        ),
        None,
    )


def company_id_from_namespace(namespace: str) -> str | None:
    """Lấy company_id từ namespace đã được backend xác thực."""

    prefix = "company-"
    return namespace[len(prefix) :] if namespace.startswith(prefix) else None


def resolve_namespace(company_id: str | None) -> str:
    """Đổi company_id thành namespace Pinecone hợp lệ và an toàn."""

    if not company_id or company_id == "all":
        return PUBLIC_NAMESPACE
    if company_id not in get_company_ids():
        raise ValueError("Công ty không tồn tại trong catalog.")
    return f"company-{company_id}"
