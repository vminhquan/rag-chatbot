"""Điều phối quy trình RAG với LLM gọi qua OpenAI API."""

from functools import lru_cache

from openai import OpenAI

from app.catalog_service import company_id_from_namespace, get_company
from app.config import get_settings
from app.pinecone_service import search_documents
from app.schema import ChatFilters, ChatMessage, ChatResponse, SourceDocument


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Tạo một OpenAI client dùng chung, đọc API key từ cấu hình."""

    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout,
    )


SYSTEM_INSTRUCTIONS = """
Bạn là trợ lý tuyển dụng của công ty.

Quy tắc bắt buộc:
- Chỉ trả lời bằng dữ liệu trong phần NGỮ CẢNH TUYỂN DỤNG.
- Không tự tạo yêu cầu, mức lương, phúc lợi hoặc vị trí tuyển dụng.
- Phân biệt rõ vị trí đang tuyển và vị trí đã đóng.
- Khi câu hỏi yêu cầu danh sách, phải đọc toàn bộ ngữ cảnh, liệt kê đầy đủ tất
  cả mục phù hợp và không dừng sau mục đầu tiên.
- Nếu ngữ cảnh không đủ, nói: "Tôi chưa tìm thấy thông tin này trong dữ
  liệu tuyển dụng hiện tại."
- Trả lời bằng tiếng Việt, thân thiện, rõ ràng và ngắn gọn.
""".strip()


def is_open_job_list_question(question: str) -> bool:
    """Nhận diện câu hỏi yêu cầu liệt kê toàn bộ vị trí đang tuyển.

    Intent này được xử lý có tính quyết định vì model local 1.5B đôi khi bỏ sót
    một mục dù Pinecone đã truy xuất đủ tài liệu.
    """

    normalized = question.casefold().strip()
    list_patterns = (
        "đang tuyển vị trí nào",
        "đang tuyển những vị trí",
        "vị trí nào đang tuyển",
        "có những vị trí nào",
        "có vị trí nào",
        "đang tuyển công việc nào",
        "đang tuyển những công việc",
        "công việc nào đang tuyển",
    )
    return any(pattern in normalized for pattern in list_patterns)


def build_open_job_list_answer(namespace: str) -> str | None:
    """Tạo câu trả lời chính xác từ catalog, không để LLM bỏ sót vị trí."""

    company_id = company_id_from_namespace(namespace)
    if not company_id:
        return None

    company = get_company(company_id)
    if not company:
        return None

    open_jobs = [job for job in company["jobs"] if job["status"] == "open"]
    if not open_jobs:
        return f"Hiện tại **{company['name']}** chưa có vị trí đang tuyển."

    job_lines = "\n".join(
        f"- **{job['title']}** — {job['location']}, {job['employment_type']}"
        for job in open_jobs
    )
    return (
        f"Hiện tại **{company['name']}** đang tuyển {len(open_jobs)} vị trí:\n\n"
        f"{job_lines}"
    )


def build_context(documents: list[SourceDocument]) -> str:
    """Biến các kết quả Pinecone thành ngữ cảnh có cấu trúc cho GPT."""

    if not documents:
        return "Không tìm thấy tài liệu phù hợp."

    sections = []
    for number, document in enumerate(documents, start=1):
        sections.append(
            f"[Tài liệu {number}]\n"
            f"Công ty: {document.company_name or 'Không xác định'}\n"
            f"Vị trí: {document.job_title or 'Thông tin công ty'}\n"
            f"Địa điểm: {document.location or 'Không xác định'}\n"
            f"Nội dung: {document.content}"
        )
    return "\n\n".join(sections)


def build_history(history: list[ChatMessage], limit: int = 6) -> str:
    """Chỉ giữ vài tin nhắn gần nhất để prompt không tăng vô hạn."""

    if not history:
        return "Chưa có hội thoại trước đó."

    role_names = {"user": "Ứng viên", "assistant": "Trợ lý"}
    return "\n".join(
        f"{role_names[message.role]}: {message.content}"
        for message in history[-limit:]
    )


def answer_question(
    question: str,
    namespace: str,
    history: list[ChatMessage],
    filters: ChatFilters,
) -> ChatResponse:
    """Thực hiện đầy đủ một lượt hỏi đáp RAG.

    Luồng xử lý: tìm tài liệu trong Pinecone -> ghép context và lịch sử -> gọi
    OpenAI -> trả câu trả lời kèm nguồn cho frontend.
    """

    settings = get_settings()
    pinecone_filter = {
        key: {"$eq": value}
        for key, value in filters.model_dump(exclude_none=True).items()
    }
    documents = search_documents(
        question, namespace, settings.top_k, pinecone_filter or None
    )

    # Danh sách tuyển dụng là dữ liệu có cấu trúc, nên trả trực tiếp từ catalog
    # để đảm bảo không thiếu Backend/Frontend do giới hạn của model nhỏ.
    if is_open_job_list_question(question):
        exact_answer = build_open_job_list_answer(namespace)
        if exact_answer:
            job_sources = [doc for doc in documents if doc.job_title]
            return ChatResponse(answer=exact_answer, sources=job_sources)

    context = build_context(documents)
    conversation = build_history(history)

    user_input = f"""
LỊCH SỬ HỘI THOẠI:
{conversation}

NGỮ CẢNH TUYỂN DỤNG:
{context}

CÂU HỎI CỦA ỨNG VIÊN:
{question}
""".strip()

    response = get_openai_client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_input},
        ],
        temperature=0.2,
        max_tokens=600,
    )
    answer = (response.choices[0].message.content or "").strip()

    return ChatResponse(answer=answer, sources=documents)
