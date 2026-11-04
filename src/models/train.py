"""Phase 3 - compare algorithms, tune with GridSearchCV, evaluate, save with joblib."""
import json, time
from pathlib import Path
import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

SEED = 42
MODELS, REPORTS = Path("models"), Path("reports")
MODELS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)


def tfidf():
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, max_features=50000)


def compare_algorithms(train):
    """Quick comparison on a validation split carved from TRAIN (test set stays untouched)."""
    tr, va = train_test_split(train, test_size=0.2, random_state=SEED, stratify=train["label"])
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "LinearSVC": LinearSVC(class_weight="balanced"),
        "RandomForest": RandomForestClassifier(n_estimators=150, class_weight="balanced", n_jobs=-1, random_state=SEED),
    }
    res = {}
    for name, clf in candidates.items():
        pipe = Pipeline([("tfidf", tfidf()), ("clf", clf)]).fit(tr["text"], tr["label"])
        pred = pipe.predict(va["text"])
        res[name] = {"accuracy": accuracy_score(va["label"], pred),
                     "f1_macro": f1_score(va["label"], pred, average="macro")}
        print(f"{name:20s} acc={res[name]['accuracy']:.3f} f1={res[name]['f1_macro']:.3f}")
    return res


def main():
    train = pd.read_csv("data/processed/train.csv")
    test = pd.read_csv("data/processed/test.csv")
    comparison = compare_algorithms(train)

    # Logistic Regression gives calibrated probabilities (confidence) -> tune it
    pipe = Pipeline([("tfidf", tfidf()),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    grid = {"tfidf__ngram_range": [(1, 1), (1, 2)],
            "clf__C": [1, 3, 10, 30]}
    gs = GridSearchCV(pipe, grid, scoring="f1_macro", cv=3, n_jobs=-1, verbose=1)
    gs.fit(train["text"], train["label"])
    print("Best params:", gs.best_params_, "| CV f1_macro:", round(gs.best_score_, 4))

    best = gs.best_estimator_
    vec, clf = best.named_steps["tfidf"], best.named_steps["clf"]
    joblib.dump(vec, MODELS / "tfidf_vectorizer.joblib")
    joblib.dump(clf, MODELS / "sentiment_model.joblib")

    # ---- evaluation on held-out test set
    pred = best.predict(test["text"])
    report = classification_report(test["label"], pred, output_dict=True, digits=3)
    print(classification_report(test["label"], pred, digits=3))

    # ---- inference time for a batch of 50
    batch = test["text"].head(50).tolist()
    t0 = time.perf_counter()
    for _ in range(20):
        clf.predict_proba(vec.transform(batch))
    ms = (time.perf_counter() - t0) / 20 * 1000
    print(f"Inference time (batch of 50): {ms:.1f} ms")

    metrics = {"best_params": {k: str(v) for k, v in gs.best_params_.items()},
               "accuracy": accuracy_score(test["label"], pred),
               "f1_per_class": {k: report[k]["f1-score"] for k in ("-1", "0", "1")},
               "f1_macro": report["macro avg"]["f1-score"],
               "inference_ms_batch50": ms,
               "algorithm_comparison": comparison}
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2))

    cm = confusion_matrix(test["label"], pred, labels=[-1, 0, 1])
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["neg", "neu", "pos"], yticklabels=["neg", "neu", "pos"])
    plt.xlabel("Predicted"); plt.ylabel("True"); plt.title("Confusion matrix (test)")
    plt.tight_layout(); plt.savefig(REPORTS / "confusion_matrix.png", dpi=130)

    ok = metrics["accuracy"] >= 0.80 and min(metrics["f1_per_class"].values()) > 0.75 and ms < 100
    print("Performance criteria met:", ok)


if __name__ == "__main__":
    main()
