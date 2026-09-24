"""Ingest catalog đa công ty vào các namespace Pinecone.

Chạy tất cả công ty:
    python -m scripts.ingest_data

Chỉ chạy một công ty:
    python -m scripts.ingest_data --company novatech
"""

import argparse
import hashlib

from app.catalog_service import PUBLIC_NAMESPACE, load_catalog
from app.pinecone_service import upsert_documents


def stable_id(*parts: str) -> str:
    """Tạo ID ổn định để ingest lại sẽ cập nhật record cũ, không nhân bản."""

    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:32]


def company_records(company: dict) -> list[dict]:
    """Tạo record giới thiệu, phúc lợi và từng JD cho namespace công ty."""

    common = {
        "company_id": company["id"],
        "company_name": company["name"],
        "industry": company["industry"],
        "location": company["location"],
    }
    records = [
        {
            "_id": stable_id(company["id"], "overview"),
            "text": (
                f"CÔNG TY: {company['name']}\n"
                f"NGÀNH: {company['industry']}\n"
                f"ĐỊA ĐIỂM: {company['location']}\n"
                f"GIỚI THIỆU: {company['overview']}"
            ),
            "source": f"companies.json#{company['id']}-overview",
            "record_type": "company",
            **common,
        },
        {
            "_id": stable_id(company["id"], "benefits"),
            "text": f"CÔNG TY: {company['name']}\nPHÚC LỢI: {company['benefits']}",
            "source": f"companies.json#{company['id']}-benefits",
            "record_type": "benefits",
            **common,
        },
    ]
    records.extend(job_record(company, job) for job in company["jobs"])
    return records


def job_record(company: dict, job: dict) -> dict:
    """Biến một JD thành record có metadata để Pinecone lọc chính xác."""

    status_label = "Đang tuyển" if job["status"] == "open" else "Đã đóng"
    return {
        "_id": stable_id(company["id"], job["id"]),
        "text": (
            f"CÔNG TY: {company['name']}\n"
            f"VỊ TRÍ: {job['title']}\n"
            f"TRẠNG THÁI: {status_label}\n"
            f"NGÀNH: {company['industry']}\n"
            f"NHÓM NGHỀ: {job['category']}\n"
            f"CẤP BẬC: {job['level']}\n"
            f"ĐỊA ĐIỂM: {job['location']}\n"
            f"HÌNH THỨC: {job['employment_type']}\n"
            f"MÔ TẢ: {job['description']}\n"
            f"YÊU CẦU: {job['requirements']}\n"
            f"MỨC LƯƠNG: {job['salary']}"
        ),
        "source": f"companies.json#{company['id']}-{job['id']}",
        "record_type": "job",
        "company_id": company["id"],
        "company_name": company["name"],
        "job_id": job["id"],
        "job_title": job["title"],
        "industry": company["industry"],
        "job_category": job["category"],
        "level": job["level"],
        "location": job["location"],
        "employment_type": job["employment_type"],
        "status": job["status"],
    }


def ingest_company(company: dict) -> int:
    """Upsert một công ty vào namespace riêng và JD vào public-jobs."""

    records = company_records(company)
    upsert_documents(records, f"company-{company['id']}")

    # public-jobs chỉ chứa JD để hỗ trợ tìm việc xuyên nhiều công ty.
    public_records = [record for record in records if record["record_type"] == "job"]
    upsert_documents(public_records, PUBLIC_NAMESPACE)
    return len(records)


def ingest(company_id: str | None = None) -> None:
    """Điều phối ingest tất cả hoặc một công ty trong catalog."""

    companies = load_catalog()["companies"]
    if company_id:
        companies = [company for company in companies if company["id"] == company_id]
        if not companies:
            raise ValueError(f"Không tìm thấy company_id '{company_id}'.")

    total = 0
    for company in companies:
        count = ingest_company(company)
        total += count
        print(f"Đã ingest {count} records cho {company['name']}.")

    print(
        f"Hoàn tất {len(companies)} công ty, {total} records riêng; "
        f"các JD đã đồng bộ vào '{PUBLIC_NAMESPACE}'."
    )


def parse_args() -> argparse.Namespace:
    """Đọc tham số dòng lệnh cho phép ingest chọn lọc một công ty."""

    parser = argparse.ArgumentParser(description="Ingest dữ liệu tuyển dụng")
    parser.add_argument("--company", help="Company ID; bỏ trống để ingest tất cả")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ingest(args.company)
