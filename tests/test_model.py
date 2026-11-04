import time
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score
from src.api.model_service import ModelService
from src.utils.text import clean_text


@pytest.fixture(scope="module")
def svc():
    return ModelService("models")


def test_cleaning():
    assert clean_text("Check https://x.com @bob #fun 😀 GREAT!!!") == "check great"


def test_performance_on_test_set(svc):
    df = pd.read_csv("data/processed/test.csv")
    labels, _ = svc.predict(df["text"].tolist())
    assert accuracy_score(df["label"], labels) >= 0.80
    assert f1_score(df["label"], labels, average=None).min() > 0.75


@pytest.mark.parametrize("text", ["ok", "a" * 5000, "😀😀😀", "c'est super mais it's trash", ""])
def test_edge_cases(svc, text):
    labels, conf = svc.predict([text])
    assert labels[0] in (-1, 0, 1) and 0 <= conf[0] <= 1


def test_inference_time(svc):
    batch = ["this video is great"] * 50
    t0 = time.perf_counter(); svc.predict(batch)
    assert (time.perf_counter() - t0) * 1000 < 100
