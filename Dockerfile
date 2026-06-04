FROM python:3.11-slim

# ── System dependencies ──────────────────────────
# matplotlib needs libfreetype; fonts for CJK chart labels
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# ── App ──────────────────────────────────────────
WORKDIR /app

COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

COPY . .

# ── Non-root user ────────────────────────────────
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── Matplotlib config ────────────────────────────
ENV MPLBACKEND=Agg

# ── Flask config ─────────────────────────────────
ENV FLASK_DEBUG=0
ENV PORT=8080

EXPOSE 8080

# ── Health check ─────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/status')" || exit 1

CMD ["python", "app.py"]
