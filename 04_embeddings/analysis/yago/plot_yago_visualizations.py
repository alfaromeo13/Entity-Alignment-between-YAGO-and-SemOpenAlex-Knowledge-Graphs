#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt

BASE = "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/analysis/yago"
EPOCH_CSV = os.path.join(BASE, "yago_epoch_comparison.csv")
FINAL_CSV = os.path.join(BASE, "yago_final_comparison.csv")
FIG_DIR = os.path.join(BASE, "figures")

MODELS_TO_KEEP = ["ComplEx", "DistMult", "TransE"]

os.makedirs(FIG_DIR, exist_ok=True)

def load_data():
    df_epoch = pd.read_csv(EPOCH_CSV)
    df_final = pd.read_csv(FINAL_CSV)

    df_epoch = df_epoch[df_epoch["model"].isin(MODELS_TO_KEEP)].copy()
    df_final = df_final[df_final["model"].isin(MODELS_TO_KEEP)].copy()

    # make sure numeric columns are numeric
    for col in df_epoch.columns:
        if col not in ["model"]:
            df_epoch[col] = pd.to_numeric(df_epoch[col], errors="coerce")

    for col in df_final.columns:
        if col not in ["model", "status"]:
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

    return df_epoch, df_final

def save_line_plot(df, metric_col, ylabel, filename):
    plt.figure(figsize=(8, 5))
    for model in MODELS_TO_KEEP:
        sub = df[df["model"] == model].sort_values("epoch")
        plt.plot(sub["epoch"], sub[metric_col], marker="o", label=model)

    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.title(f"YAGO: {ylabel} across epochs")
    plt.xticks(sorted(df["epoch"].dropna().unique()))
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    svg_path = os.path.join(FIG_DIR, filename + ".svg")
    pdf_path = os.path.join(FIG_DIR, filename + ".pdf")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight")
    plt.close()

    print(f"Saved: {svg_path}")
    print(f"Saved: {pdf_path}")

def main():
    df_epoch, df_final = load_data()

    # epoch curves
    save_line_plot(df_epoch, "weighted_mrr_after", "MRR", "yago_mrr_vs_epoch")
    save_line_plot(df_epoch, "weighted_hits10_after", "Hits@10", "yago_hits10_vs_epoch")
    save_line_plot(df_epoch, "weighted_auc_after", "AUC", "yago_auc_vs_epoch")
    save_line_plot(df_epoch, "weighted_train_loss", "Train Loss", "yago_train_loss_vs_epoch")

if __name__ == "__main__":
    main()
