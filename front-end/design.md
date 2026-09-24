# Thiết kế UI/UX Chatbot Widget · Hallmark

Hệ thiết kế khóa theo Hallmark: genre `modern-minimal`, theme `Cobalt`, đối
tượng là ứng viên và tác vụ chính là tìm thông tin tuyển dụng đáng tin cậy.

## 1. Thông số màu sắc

- Primary: token `--color-accent` theo OKLCH Cobalt.
- Background: token `--color-canvas`.
- Bong bóng user: gradient Blue 600–700, chữ trắng.
- Bong bóng bot: nền trắng, viền Slate 200, chữ Slate 800.
- Success/online: `#86EFAC`.
- Error: nền `#FEF2F2`, chữ `#B91C1C`.

## 2. Kiểu chữ

- Font display: Manrope; font nội dung: DM Sans.
- Tin nhắn: `13px`, line-height `1.55`.
- Có system-font fallback nếu Google Fonts không tải được.

## 3. Thành phần tương tác

- Chat container: rộng tối đa `380px`, cao `600px`, bo góc `20px`.
- Header: tên TalentBot, badge AI, trạng thái online/typing và nút reset.
- Message Area: user bên phải, bot bên trái, Markdown/GFM và code block.
- Quick Suggestions: ba chip câu hỏi tuyển dụng, tự ẩn sau tin nhắn đầu tiên.
- Input Bar: textarea tự tăng chiều cao, nút tệp và nút gửi.
- Enter để gửi; Shift + Enter để xuống dòng.
- Attachment hiện chỉ chọn và hiển thị tên file. API backend chưa nhận upload.

## 4. Responsive và accessibility

- Desktop hiển thị dạng widget giữa màn hình.
- Màn hình dưới `480px` chuyển sang toàn màn hình.
- Có `aria-label`, trạng thái lỗi và vùng chat `aria-live`.
- Hỗ trợ `prefers-reduced-motion`.
- Kiểm tra responsive tại 320, 375, 414 và 768px; root dùng `overflow-x: clip`.

## 5. API contract

- Base URL lấy từ `VITE_API_BASE_URL`.
- Endpoint: `POST /api/chat`.
- Request: `{ "question": string, "history": ChatMessage[] }`.
- Response: `{ "answer": string, "sources": SourceDocument[] }`.
