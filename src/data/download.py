"""Phase 2 - download the Reddit sentiment dataset and print statistics."""
from pathlib import Path
import requests
import pandas as pd

URL = ("https://raw.githubusercontent.com/Himanshu-1703/"
       "reddit-sentiment-analysis/refs/heads/main/data/reddit.csv")
OUT = Path("data/raw/reddit.csv")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    OUT.write_bytes(r.content)
    df = pd.read_csv(OUT)
    print(f"Saved to {OUT}")
    print(f"Comments: {len(df)} | columns: {list(df.columns)}")
    print("Label distribution:")
    print(df["category"].value_counts().sort_index().rename({-1: "-1 (neg)", 0: "0 (neu)", 1: "1 (pos)"}))


if __name__ == "__main__":
    main()
