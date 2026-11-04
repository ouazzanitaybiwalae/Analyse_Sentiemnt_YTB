FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -m -u 1000 user
WORKDIR /app

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY --chown=user src/ ./src/
COPY --chown=user models/ ./models/
COPY --chown=user app_api.py .

USER user
EXPOSE 7860
ENV PORT=7860
CMD ["sh", "-c", "uvicorn app_api:app --host 0.0.0.0 --port ${PORT}"]