# services/embed: embedding and rerank service

bge-reranker-v2-m3 (sentence-transformers, CPU) behind a small FastAPI app on the GPU machine, reached through the gateway at `/embed`. BGE-M3 embeddings (1024-d, multilingual) are served by Ollama on the AMD GPU (`bge-m3` model).
