import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Bot,
  BriefcaseBusiness,
  Building2,
  Gift,
  Paperclip,
  RefreshCw,
  ChevronDown,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const QUICK_SUGGESTIONS = [
  { icon: BriefcaseBusiness, label: "Đang tuyển vị trí nào?" },
  { icon: Building2, label: "Giới thiệu về công ty" },
  { icon: Gift, label: "Phúc lợi nhân viên ra sao?" },
];

const WELCOME_MESSAGE = {
  id: "welcome",
  role: "assistant",
  content:
    "Xin chào! Mình là **MQBot**, trợ lý tuyển dụng. **Bạn muốn hỏi về công ty nào?**",
  createdAt: new Date(),
};

function formatTime(date) {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <article className={`message-row ${isUser ? "message-row--user" : ""}`}>
      {!isUser && (
        <div className="bot-avatar" aria-hidden="true">
          <Bot size={17} strokeWidth={2.25} />
        </div>
      )}

      <div className="message-content">
        <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--bot"}`}>
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          )}
        </div>
        <time className="message-time" dateTime={message.createdAt.toISOString()}>
          {formatTime(message.createdAt)}
        </time>
        {!isUser && message.sources?.length > 0 && (
          <details className="message-sources">
            <summary>
              {message.sources.length} nguồn tham khảo <ChevronDown size={13} />
            </summary>
            <div>
              {message.sources.map((source) => (
                <p key={source.id}>
                  {source.company_name || source.source}
                  {source.job_title ? ` · ${source.job_title}` : ""}
                </p>
              ))}
            </div>
          </details>
        )}
      </div>
    </article>
  );
}

function TypingIndicator() {
  return (
    <div className="message-row" aria-label="Trợ lý đang soạn câu trả lời">
      <div className="bot-avatar bot-avatar--typing">
        <Bot size={17} />
      </div>
      <div className="typing-bubble">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState("");
  const [requestState, setRequestState] = useState("default");
  const [catalog, setCatalog] = useState({ companies: [], industries: [], locations: [] });
  const [companyId, setCompanyId] = useState("");
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const messageEndRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/catalog`);
        if (!response.ok) throw new Error("Không tải được danh mục công ty.");
        setCatalog(await response.json());
      } catch (catalogError) {
        setError(catalogError.message);
      }
    };
    loadCatalog();
  }, []);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 112)}px`;
  }, [input]);

  const resetChat = () => {
    setMessages([{ ...WELCOME_MESSAGE, createdAt: new Date() }]);
    setInput("");
    setSelectedFile(null);
    setError("");
    setRequestState("default");
    setCompanyId("");
    textareaRef.current?.focus();
  };

  const selectCompany = (company) => {
    setCompanyId(company.id);
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: company.name,
        createdAt: new Date(),
      },
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Bạn đang tìm hiểu về **${company.name}**. Bạn có thể hỏi về vị trí đang tuyển, yêu cầu công việc hoặc phúc lợi của công ty.`,
        createdAt: new Date(),
      },
    ]);
    setError("");
    textareaRef.current?.focus();
  };

  const sendMessage = async (question = input) => {
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isTyping || !companyId) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: cleanQuestion,
      createdAt: new Date(),
    };
    const history = messages
      .filter((message) => message.id !== "welcome")
      .map(({ role, content }) => ({ role, content }));

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError("");
    setIsTyping(true);
    setRequestState("loading");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: cleanQuestion,
          company_id: companyId,
          history,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || `API trả về lỗi ${response.status}`);
      }

      const data = await response.json();
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
          createdAt: new Date(),
        },
      ]);
      setRequestState("success");
    } catch (requestError) {
      setError(
        requestError.message || "Không thể kết nối tới máy chủ. Vui lòng thử lại.",
      );
      setRequestState("error");
    } finally {
      setIsTyping(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) setSelectedFile(file);
    event.target.value = "";
  };

  return (
    <main className="page-shell">
      <section className="chat-card" data-state={requestState} aria-label="Trợ lý tuyển dụng MQBot">
        <header className="chat-header">
          <div className="brand-mark" aria-hidden="true">
            <Bot size={20} />
          </div>
          <div className="brand-copy">
            <span className="brand-kicker">RECRUITING DESK</span>
            <div className="brand-title-row">
              <h1>MQBot</h1>
            </div>
            <p>
              <span className={`status-dot ${isTyping ? "status-dot--typing" : ""}`} />
              {isTyping ? "Đang trả lời..." : "Đang hoạt động"}
            </p>
          </div>
          <button className="icon-button reset-button" type="button" onClick={resetChat} aria-label="Làm mới cuộc trò chuyện" title="Làm mới cuộc trò chuyện">
            <RefreshCw size={18} />
          </button>
        </header>

        <div className="message-area" aria-live="polite">
          <div className="welcome-date">Hôm nay</div>
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          {!companyId && (
            <div className="company-picker" aria-label="Chọn công ty muốn tìm hiểu">
              {catalog.companies.map((company) => (
                <button key={company.id} type="button" onClick={() => selectCompany(company)}>
                  <span className="company-monogram">{company.name.charAt(0)}</span>
                  <span>
                    <strong>{company.name}</strong>
                    <small>{company.industry} · {company.location}</small>
                  </span>
                  <ArrowUp size={14} />
                </button>
              ))}
            </div>
          )}
          {isTyping && <TypingIndicator />}
          {error && (
            <div className="error-banner" role="alert">
              {error}
              <button type="button" onClick={() => setError("")} aria-label="Đóng thông báo lỗi">
                <X size={15} />
              </button>
            </div>
          )}
          <div ref={messageEndRef} />
        </div>

        <footer className="composer-section">
          {companyId && messages.length === 3 && (
            <div className="suggestion-block">
              <p>Có thể bạn muốn hỏi</p>
              <div className="suggestions" aria-label="Câu hỏi gợi ý">
                {QUICK_SUGGESTIONS.map(({ icon: Icon, label }) => (
                  <button key={label} type="button" onClick={() => sendMessage(label)}>
                    <Icon size={15} />
                    <span>{label}</span>
                    <ArrowUp className="suggestion-arrow" size={14} />
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedFile && (
            <div className="file-pill">
              <Paperclip size={13} />
              <span>{selectedFile.name}</span>
              <button type="button" onClick={() => setSelectedFile(null)} aria-label="Bỏ tệp đã chọn">
                <X size={13} />
              </button>
            </div>
          )}

          <div className="composer">
            <input ref={fileInputRef} type="file" hidden onChange={handleFileChange} accept=".pdf,.doc,.docx,.txt" />
            <button className="icon-button attach-button" type="button" onClick={() => fileInputRef.current?.click()} aria-label="Đính kèm tệp" title="Đính kèm tệp">
              <Paperclip size={19} />
            </button>
            <textarea
              ref={textareaRef}
              rows="1"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi của bạn..."
              disabled={!companyId}
              aria-label="Nội dung câu hỏi"
            />
            <button className="send-button" data-state={requestState} type="button" onClick={() => sendMessage()} disabled={!companyId || !input.trim() || isTyping} aria-label="Gửi câu hỏi">
              <ArrowUp size={19} strokeWidth={2.5} />
            </button>
          </div>
          <p className="composer-hint">{companyId ? "MQBot có thể mắc lỗi. Hãy kiểm tra lại thông tin quan trọng." : "Chọn một công ty để bắt đầu trò chuyện."}</p>
        </footer>
      </section>
    </main>
  );
}
