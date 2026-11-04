"""FastAPI application (Phase 4)."""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.model_service import NAMES, ModelService
from src.api.schemas import BatchRequest, BatchResponse, HealthResponse, Prediction, Statistics
from src.utils.logger import get_logger

log = get_logger("api")
VERSION = "1.0.0"
state: dict = {"service": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["service"] = ModelService()      # loaded once, reused by every request
        log.info("Model loaded")
    except Exception as e:                     # API still starts; /health reports the problem
        log.error("Model loading failed: %s", e)
    yield


app = FastAPI(title="YouTube Sentiment API", version=VERSION, lifespan=lifespan)

# Chrome extensions send an Origin like chrome-extension://<id>; allow it (and the dev tools).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "Invalid request",
                                                  "detail": "Body must be {\"comments\": [\"text\", ...]} with 1-1000 strings."})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/")
def root():
    return {"name": "YouTube Sentiment API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse)
def health():
    loaded = state["service"] is not None
    return HealthResponse(status="ok" if loaded else "degraded", model_loaded=loaded, version=VERSION)


@app.post("/predict_batch", response_model=BatchResponse)
def predict_batch(req: BatchRequest):
    service = state["service"]
    if service is None:
        return JSONResponse(status_code=503, content={"error": "Model not loaded"})
    t0 = time.perf_counter()
    labels, conf = service.predict(req.comments)
    preds = [Prediction(index=i, text=t, label=l, sentiment=NAMES[l], confidence=round(c, 4))
             for i, (t, l, c) in enumerate(zip(req.comments, labels, conf))]
    n = len(preds)
    counts = {name: sum(1 for p in preds if p.sentiment == name) for name in NAMES.values()}
    stats = Statistics(total=n, counts=counts,
                       percentages={k: round(v / n * 100, 1) for k, v in counts.items()},
                       average_confidence=round(sum(conf) / n, 4))
    ms = (time.perf_counter() - t0) * 1000
    log.info("predict_batch n=%d time=%.1fms", n, ms)
    return BatchResponse(predictions=preds, statistics=stats, processing_ms=round(ms, 2))
