"""Tạo Pinecone index tích hợp model llama-text-embed-v2.

Chạy một lần trước khi ingest dữ liệu:
    python -m scripts.create_index
"""

import time

from pinecone import Pinecone

from app.config import get_settings


def create_index_if_not_exists() -> None:
    """Tạo index nếu chưa tồn tại và chờ đến khi index sẵn sàng."""

    settings = get_settings()
    client = Pinecone(api_key=settings.pinecone_api_key)
    index_name = settings.pinecone_index_name

    if client.has_index(index_name):
        print(f"Index '{index_name}' đã tồn tại, không cần tạo lại.")
        return

    client.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model": "llama-text-embed-v2",
            # Pinecone sẽ embedding nội dung của trường chunk_text.
            "field_map": {"text": "text"},
        },
    )

    # Việc tạo index là bất đồng bộ nên cần đợi trước khi ingest.
    while not client.describe_index(index_name).status["ready"]:
        print("Đang chờ Pinecone index sẵn sàng...")
        time.sleep(2)

    print(f"Đã tạo thành công index '{index_name}'.")


if __name__ == "__main__":
    create_index_if_not_exists()
