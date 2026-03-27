import pandas as pd

INPUT_FILE = "withoutGroupings_output.csv"
OUTPUT_FILE = "eval_ready.csv"

# Columns from structure_data (lines 13–27), with defaults.
# If a name would duplicate an existing column (case-insensitive), we skip or use an alias.
REVIEW_DEFAULTS = [
    ("ID", None),  # filled below if missing
    ("Category", "Unassigned"),
    ("Accuracy Score A", ""),
    ("Accuracy Score B", ""),
    ("Helpfulness Score A", ""),
    ("Helpfulness Score B", ""),
    ("Tone Score A", ""),
    ("Tone Score B", ""),
    ("Conciseness Score A", ""),
    ("Conciseness Score B", ""),
    ("Win", ""),  # A, B, or Tie
    ("Win Reason", ""),
    ("Reviewer Notes", ""),
    ("Review Status", "Unreviewed"),
]

# If output already has `category` (topic), use this name for reviewer “Category” instead.
REVIEWER_CATEGORY_COL = "ReviewerCategory"


def _existing_lower(df):
    return {c.lower(): c for c in df.columns}


def add_column_if_absent(df, name, default):
    """Add column only if `name` is not already present (case-insensitive)."""
    lower = _existing_lower(df)
    if name.lower() in lower:
        return df
    df[name] = default
    return df


df = pd.read_csv(INPUT_FILE)
existing_lower = _existing_lower(df)

# ID: add sequential IDs only if missing
if "id" not in existing_lower:
    df.insert(0, "ID", range(1, len(df) + 1))
    existing_lower = _existing_lower(df)

for col, default in REVIEW_DEFAULTS:
    if col == "ID":
        continue
    if col == "Category":
        # Avoid duplicate with `category` from withoutGroupings_output (topic labels)
        if "category" in existing_lower:
            add_column_if_absent(df, REVIEWER_CATEGORY_COL, "Unassigned")
        else:
            add_column_if_absent(df, "Category", default)
        existing_lower = _existing_lower(df)
        continue
    add_column_if_absent(df, col, default)
    existing_lower = _existing_lower(df)

df.to_csv(OUTPUT_FILE, index=False)
print(f"Wrote {len(df)} rows to {OUTPUT_FILE}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
