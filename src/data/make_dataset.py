"""Phase 2 - clean raw data, save processed CSV ('text','label') and a reproducible split."""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from src.utils.text import clean_text

RAW = Path("data/raw/reddit.csv")
PROC = Path("data/processed")
SEED, TEST_SIZE = 42, 0.2


def main():
    df = pd.read_csv(RAW).rename(columns={"clean_comment": "text", "category": "label"})
    df = df[["text", "label"]].dropna()
    df["text"] = df["text"].map(clean_text)
    df = df[df["text"].str.len() > 0].drop_duplicates(subset="text")
    df["label"] = df["label"].astype(int)

    PROC.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROC / "clean.csv", index=False)

    # stratified + fixed seed => same split on every run
    train, test = train_test_split(df, test_size=TEST_SIZE, random_state=SEED, stratify=df["label"])
    train.to_csv(PROC / "train.csv", index=False)
    test.to_csv(PROC / "test.csv", index=False)
    print(f"clean={len(df)} train={len(train)} test={len(test)}")
    print(df["label"].value_counts().sort_index())


if __name__ == "__main__":
    main()
