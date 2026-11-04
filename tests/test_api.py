import time
from fastapi.testclient import TestClient
from src.api.main import app


def test_health():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200 and r.json()["model_loaded"] is True


def test_predict_batch_sizes():
    with TestClient(app) as c:
        for n in (1, 10, 50, 200):
            r = c.post("/predict_batch", json={"comments": ["I love this video, amazing!"] * n})
            body = r.json()
            assert r.status_code == 200
            assert body["statistics"]["total"] == n and len(body["predictions"]) == n


def test_sentiment_direction():
    with TestClient(app) as c:
        r = c.post("/predict_batch", json={"comments": ["This is amazing, I love it", "Terrible, I hate this garbage"]})
        p = r.json()["predictions"]
        assert p[0]["sentiment"] == "positive" and p[1]["sentiment"] == "negative"


def test_errors():
    with TestClient(app) as c:
        assert c.post("/predict_batch", json={"comments": []}).status_code == 422
        assert c.post("/predict_batch", json={"comments": [1, 2]}).status_code == 422
        assert c.post("/predict_batch", json={"wrong": "x"}).status_code == 422
        assert c.post("/predict_batch", content="not json").status_code == 422


def test_response_time():
    with TestClient(app) as c:
        t0 = time.perf_counter()
        c.post("/predict_batch", json={"comments": ["nice"] * 50})
        assert (time.perf_counter() - t0) < 1.0
