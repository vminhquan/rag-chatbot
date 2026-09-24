"""Các schema định nghĩa dữ liệu vào/ra của REST API."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Một tin nhắn cũ dùng để GPT hiểu ngữ cảnh hội thoại gần nhất."""

    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatFilters(BaseModel):
    """Các điều kiện tùy chọn khi tìm việc trong public-jobs."""

    industry: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern="^(open|closed)$")


class ChatRequest(BaseModel):
    """Dữ liệu ReactJS gửi đến endpoint POST /api/chat."""

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Câu hỏi của ứng viên",
    )
    company_id: str | None = Field(
        default="all",
        max_length=100,
        description="ID công ty trong catalog hoặc 'all' để tìm toàn hệ thống",
    )
    filters: ChatFilters = Field(default_factory=ChatFilters)
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Lịch sử hội thoại gần nhất do frontend gửi lên",
    )


class SourceDocument(BaseModel):
    """Một đoạn tài liệu Pinecone đã dùng để tạo câu trả lời."""

    id: str
    content: str
    source: str
    score: float
    company_id: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    industry: str | None = None
    location: str | None = None
    status: str | None = None


class ChatResponse(BaseModel):
    """Dữ liệu backend trả về cho ReactJS."""

    answer: str
    sources: list[SourceDocument]


class HealthResponse(BaseModel):
    """Kết quả kiểm tra trạng thái sống của API."""

    status: str


class CompanySummary(BaseModel):
    """Thông tin công ty dùng trong dropdown frontend."""

    id: str
    name: str
    industry: str
    location: str


class CatalogResponse(BaseModel):
    """Danh mục công ty và các lựa chọn bộ lọc."""

    companies: list[CompanySummary]
    industries: list[str]
    locations: list[str]
