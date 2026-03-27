from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("eval_scored.csv")

AIRTABLE_DIR = Path("airtable_exports")
TOP_SCORE_GAPS_N = 25

# (label for charts, column prefix in CSV)
DIMENSIONS = [
    ("Correctness", "correctness"),
    ("Helpfulness", "helpfulness"),
    ("Tone", "tone"),
    ("Conciseness", "conciseness"),
]

print(f"Total evaluated: {len(df)}")

# ── Win Rate ──────────────────────────────────────────
win_counts = df["model_winner"].value_counts()
print("\n=== Overall Win Rate ===")
print(win_counts)
print(f"\nModel A Win Rate: {(win_counts.get('Model A', 0)/len(df)*100):.1f}%")
print(f"Model B Win Rate: {(win_counts.get('Model B', 0)/len(df)*100):.1f}%")
print(f"Tie Rate: {(win_counts.get('Tie', 0)/len(df)*100):.1f}%")

# ── Average scores by dimension ───────────────────────
print("\n=== Average Scores by Dimension ===")
for label, prefix in DIMENSIONS:
    avg_a = df[f"{prefix}_a"].mean()
    avg_b = df[f"{prefix}_b"].mean()
    winner = "Model A" if avg_a > avg_b else "Model B" if avg_b > avg_a else "Tie"
    print(f"{label}: Model A={avg_a:.2f} | Model B={avg_b:.2f} | Winner: {winner}")

# ── Win rate by category ──────────────────────────────
print("\n=== Win Rate by Category ===")
category_wins = df.groupby(["category", "model_winner"]).size().unstack(fill_value=0)
print(category_wins)

# ── Most common win reasons ───────────────────────────
print("\n=== Top Win Reasons ===")
print(df["win_reason"].value_counts())

# ── Biggest score gaps (most decisive wins) ───────────
df["score_gap"] = abs(
    (
        df["correctness_a"]
        + df["helpfulness_a"]
        + df["tone_a"]
        + df["conciseness_a"]
    )
    - (
        df["correctness_b"]
        + df["helpfulness_b"]
        + df["tone_b"]
        + df["conciseness_b"]
    )
)
print("\n=== Top 5 Most Decisive Wins (by total score gap) ===")
print(
    df.nlargest(5, "score_gap")[
        ["ID", "prompt", "model_winner", "win_reason", "score_gap"]
    ].to_string(index=False)
)

# ── Visualizations ────────────────────────────────────
dim_labels = [d[0] for d in DIMENSIONS]
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(
    "Claude Model A vs Model B — Customer Service Eval",
    fontsize=14,
    fontweight="bold",
)

# Chart 1: Win rate pie chart
colors = ["#4CAF50", "#FF9800", "#2196F3"]
axes[0, 0].pie(
    win_counts.values,
    labels=win_counts.index,
    autopct="%1.1f%%",
    colors=colors[: len(win_counts)],
)
axes[0, 0].set_title("Overall Win Rate (model_winner)")

# Chart 2: Average scores by dimension
x = np.arange(len(DIMENSIONS))
width = 0.35
scores_a = [df[f"{p}_a"].mean() for _, p in DIMENSIONS]
scores_b = [df[f"{p}_b"].mean() for _, p in DIMENSIONS]
axes[0, 1].bar(x - width / 2, scores_a, width, label="Model A", color="#4CAF50")
axes[0, 1].bar(x + width / 2, scores_b, width, label="Model B", color="#2196F3")
axes[0, 1].set_xticks(x)
axes[0, 1].set_xticklabels(dim_labels)
axes[0, 1].set_ylim(0, 5)
axes[0, 1].set_title("Average Score by Dimension")
axes[0, 1].legend()

# Chart 3: Win rate by category
category_wins.plot(
    kind="bar",
    ax=axes[1, 0],
    color=["#4CAF50", "#FF9800", "#2196F3"][: category_wins.shape[1]],
)
axes[1, 0].set_title("Wins by Category")
axes[1, 0].tick_params(axis="x", rotation=45)
axes[1, 0].legend(title="model_winner")

# Chart 4: Win reason distribution
df["win_reason"].value_counts().plot(kind="bar", ax=axes[1, 1], color="#9C27B0")
axes[1, 1].set_title("Top Win Reasons")
axes[1, 1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("model_eval_results.png", dpi=150, bbox_inches="tight")
print("\nCharts saved as model_eval_results.png")

# ── Airtable-friendly CSV exports ─────────────────────
AIRTABLE_DIR.mkdir(parents=True, exist_ok=True)

n_rows = len(df)
outcomes = ["Model A", "Model B", "Tie"]
overall_rows = []
for outcome in outcomes:
    cnt = int(win_counts.get(outcome, 0))
    overall_rows.append(
        {
            "outcome": outcome,
            "count": cnt,
            "pct_of_rows": round(100 * cnt / n_rows, 2) if n_rows else 0.0,
        }
    )
pd.DataFrame(overall_rows).to_csv(
    AIRTABLE_DIR / "overall_win_rate.csv", index=False
)

dim_rows = []
for label, prefix in DIMENSIONS:
    avg_a = df[f"{prefix}_a"].mean()
    avg_b = df[f"{prefix}_b"].mean()
    winner = "Model A" if avg_a > avg_b else "Model B" if avg_b > avg_a else "Tie"
    dim_rows.append(
        {
            "dimension": label,
            "model_a_avg": round(float(avg_a), 4),
            "model_b_avg": round(float(avg_b), 4),
            "winner": winner,
        }
    )
pd.DataFrame(dim_rows).to_csv(
    AIRTABLE_DIR / "average_scores_by_dimension.csv", index=False
)

cat_wide = category_wins.copy().reset_index()
for col in outcomes:
    if col not in cat_wide.columns:
        cat_wide[col] = 0
cat_wide = cat_wide[["category"] + outcomes]
cat_wide["total_in_category"] = cat_wide[outcomes].sum(axis=1)
cat_wide.columns = [
    "category",
    "model_a_wins",
    "model_b_wins",
    "ties",
    "total_in_category",
]
cat_wide.to_csv(AIRTABLE_DIR / "win_rate_by_category.csv", index=False)

cat_long = cat_wide.melt(
    id_vars=["category"],
    value_vars=["model_a_wins", "model_b_wins", "ties"],
    var_name="outcome_key",
    value_name="count",
)
cat_long.to_csv(AIRTABLE_DIR / "win_rate_by_category_long.csv", index=False)

reasons = (
    df["win_reason"]
    .value_counts()
    .rename_axis("win_reason")
    .reset_index(name="count")
)
reasons["pct_of_rows"] = round(100 * reasons["count"] / n_rows, 2) if n_rows else 0.0
reasons.to_csv(AIRTABLE_DIR / "win_reasons.csv", index=False)

gaps = df.nlargest(TOP_SCORE_GAPS_N, "score_gap")[
    ["ID", "prompt", "model_winner", "win_reason", "score_gap"]
].copy()
gaps.insert(0, "rank", range(1, len(gaps) + 1))
gaps.to_csv(AIRTABLE_DIR / "top_score_gaps.csv", index=False)

print(
    f"\nAirtable CSVs written to {AIRTABLE_DIR.resolve()}/\n"
    "  • overall_win_rate.csv\n"
    "  • average_scores_by_dimension.csv\n"
    "  • win_rate_by_category.csv (wide)\n"
    "  • win_rate_by_category_long.csv (long — easy grouped charts)\n"
    "  • win_reasons.csv\n"
    "  • top_score_gaps.csv"
)
