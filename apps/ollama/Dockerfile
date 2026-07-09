FROM ollama/ollama:latest

# V3 OPS-V3-02: 启动时自动 pull 默认模型 qwen2.5:7b
COPY entrypoint.sh /usr/local/bin/aios-ollama-entrypoint.sh
RUN chmod +x /usr/local/bin/aios-ollama-entrypoint.sh

# 默认模型：V2/V3 一致。也可通过环境变量 AIOS_OLLAMA_PULL_MODELS 覆盖（逗号分隔）
ENV AIOS_OLLAMA_PULL_MODELS="qwen2.5:7b"

ENTRYPOINT ["/usr/local/bin/aios-ollama-entrypoint.sh"]
