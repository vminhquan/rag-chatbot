FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /llama

RUN git clone https://github.com/ggerganov/llama.cpp.git .

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --target llama-server -j1

EXPOSE 8080

# Một slot và context 2048 giúp giảm KV cache/RAM trong Docker. Alias phải
# trùng LLAMA_MODEL mà backend gửi tới API Chat Completions.
CMD ["./build/bin/llama-server", "-m", "/models/qwen2.5-1.5b-instruct-q4_k_m.gguf", "--alias", "qwen2.5-1.5b-instruct", "--host", "0.0.0.0", "--port", "8080", "-c", "2048", "-np", "1"]
