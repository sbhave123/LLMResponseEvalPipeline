"""
Fill conciseness_a / conciseness_b and win_reason in eval_scored.csv.

Conciseness heuristic (1–5)
-------------------------
Character-length buckets failed because support replies are typically 400–700+
characters, so every row scored the same.

We combine two signals, then average (rounded to an integer 1–5):

1) Word-count score (absolute brevity for a chat reply)
   - 5: ≤ 75 words
   - 4: 76–90
   - 3: 91–105
   - 2: 106–120
   - 1: 121+ words

2) Verbosity ratio = response_words / max(prompt_words, 1)
   Penalizes long answers relative to a short customer question.
   - 5: ratio ≤ 10
   - 4: ratio ≤ 14
   - 3: ratio ≤ 18
   - 2: ratio ≤ 22
   - 1: ratio > 22

Final conciseness = round((word_score + ratio_score) / 2), clipped to 1–5.
"""
import pandas as pd

INPUT = "eval_scored.csv"
OUTPUT = "eval_scored.csv"


def word_count(text) -> int:
    if pd.isna(text):
        return 0
    return len(str(text).split())


def score_word_count(words: int):
    if words <= 0:
        return pd.NA
    if words <= 75:
        return 5
    if words <= 90:
        return 4
    if words <= 105:
        return 3
    if words <= 120:
        return 2
    return 1


def score_verbosity_ratio(ratio: float):
    if pd.isna(ratio):
        return pd.NA
    if ratio <= 10:
        return 5
    if ratio <= 14:
        return 4
    if ratio <= 18:
        return 3
    if ratio <= 22:
        return 2
    return 1


def conciseness_score(response, prompt) -> int:
    rw = word_count(response)
    pw = max(word_count(prompt), 1)
    if rw <= 0:
        return pd.NA
    ratio = rw / pw
    w_score = score_word_count(rw)
    r_score = score_verbosity_ratio(ratio)
    if pd.isna(w_score) or pd.isna(r_score):
        return pd.NA
    return int(round((w_score + r_score) / 2))


def win_reason(row) -> str:
    scores = {
        "More Accurate": row["correctness_a"] - row["correctness_b"],
        "More Helpful": row["helpfulness_a"] - row["helpfulness_b"],
        "Better Tone": row["tone_a"] - row["tone_b"],
        "More Concise": row["conciseness_a"] - row["conciseness_b"],
    }
    return max(scores, key=lambda k: abs(scores[k]))


def main():
    df = pd.read_csv(INPUT)
    df["conciseness_a"] = [
        conciseness_score(r, p) for r, p in zip(df["response_model_a"], df["prompt"])
    ]
    df["conciseness_b"] = [
        conciseness_score(r, p) for r, p in zip(df["response_model_b"], df["prompt"])
    ]
    df["win_reason"] = df.apply(win_reason, axis=1)
    df.to_csv(OUTPUT, index=False)
    print(f"Updated {len(df)} rows in {OUTPUT}")
    print("conciseness_a:", df["conciseness_a"].value_counts().sort_index().to_dict())
    print("conciseness_b:", df["conciseness_b"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
