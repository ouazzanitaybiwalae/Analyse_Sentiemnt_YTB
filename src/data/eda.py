"""Phase 2 - exploratory analysis: class distribution + text length."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("reports"); OUT.mkdir(exist_ok=True)
df = pd.read_csv("data/processed/clean.csv")
df["n_words"] = df["text"].str.split().str.len()

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
df["label"].value_counts().sort_index().plot.bar(ax=ax[0], color=["#d14b4b", "#8a94a0", "#2f8f5b"])
ax[0].set_title("Class distribution (-1 / 0 / 1)")
for lab, g in df.groupby("label"):
    ax[1].hist(g["n_words"].clip(upper=100), bins=40, alpha=.5, label=str(lab))
ax[1].set_title("Text length (words, clipped at 100)"); ax[1].legend()
plt.tight_layout(); plt.savefig(OUT / "eda.png", dpi=130)
print(df.groupby("label")["n_words"].describe().round(1))
print("Imbalance handled with class_weight='balanced' during training.")
