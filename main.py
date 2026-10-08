"""Điểm khởi động REST API để frontend ReactJS gọi vào."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.catalog_service import get_companies, resolve_namespace
from app.config import get_settings
from app.rag_service import answer_question
from app.schema import CatalogResponse, ChatRequest, ChatResponse


settings = get_settings()

app = FastAPI(
    title="Recruitment RAG Chatbot API",
    version="1.0.0",
    description="API hỏi đáp thông tin công ty và các vị trí tuyển dụng.",
)

# Cho phép ứng dụng React ở origin đã cấu hình gọi API từ trình duyệt.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.get("/api/catalog", response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    """Cung cấp danh sách công ty/ngành/địa điểm cho bộ lọc React."""

    companies = get_companies()
    return CatalogResponse(
        companies=companies,
        industries=sorted({company["industry"] for company in companies}),
        locations=sorted({company["location"] for company in companies}),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Nhận câu hỏi từ ReactJS và trả lời bằng quy trình RAG."""

    try:
        namespace = resolve_namespace(request.company_id)
        return answer_question(
            request.question, namespace, request.history, request.filters
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Không trả API key hoặc stack trace cho phía frontend.
        raise HTTPException(
            status_code=500,
            detail="Không thể xử lý câu hỏi ở thời điểm hiện tại.",
        ) from exc
