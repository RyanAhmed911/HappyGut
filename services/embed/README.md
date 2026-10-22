# services/embed: rerank service

bge-reranker-v2-m3 (sentence-transformers on the machine's native ROCm PyTorch, GPU) behind a small FastAPI app on `127.0.0.1:8001`, reached through the gateway at `/embed`. Runs natively, not in Docker. BGE-M3 embeddings (1024-d, multilingual) are served by Ollama (`bge-m3`).
