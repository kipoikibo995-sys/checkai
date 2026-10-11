# CheckAI on Hugging Face Spaces (free CPU tier).
# Copy this file into a Docker Space. On each build it pulls the latest
# code from GitHub and bakes the two Qwen2.5-0.5B models into the image,
# so the app starts without downloading anything.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Spaces run containers as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

# CPU-only PyTorch is much smaller than the default CUDA build
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --user "transformers>=4.40"

RUN python -c "from huggingface_hub import snapshot_download as get; \
[get(m) for m in ('Qwen/Qwen2.5-0.5B', 'Qwen/Qwen2.5-0.5B-Instruct')]"

# Changes whenever main gets a new commit, so a rebuild always pulls fresh code
ADD https://api.github.com/repos/kipoikibo995-sys/checkai/commits/main /tmp/latest-commit.json
RUN git clone --depth 1 https://github.com/kipoikibo995-sys/checkai .

EXPOSE 7860
CMD ["python", "-m", "aicheck", "serve", "--host", "0.0.0.0", "--port", "7860"]
