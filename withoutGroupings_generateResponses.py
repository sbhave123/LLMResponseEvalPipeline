import pandas as pd
import os
import re
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Load API key
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DEFAULT_MODEL_A = "claude-haiku-4-5-20251001"
DEFAULT_MODEL_B = "claude-sonnet-4-20250514"
MODEL_A = os.getenv("ANTHROPIC_MODEL_A", DEFAULT_MODEL_A)
MODEL_B = os.getenv("ANTHROPIC_MODEL_B", DEFAULT_MODEL_B)
INPUT_FILE = os.getenv("EVAL_INPUT_FILE", "withoutGroupings_data_enhanced.csv")
OUTPUT_FILE = os.getenv("EVAL_OUTPUT_FILE", "withoutGroupings_output.csv")


def resolve_model_name(client, preferred_model):
    """Return a valid model ID for this API key."""
    try:
        model_ids = [m.id for m in client.models.list(limit=50).data]
    except Exception as e:
        print(f"Could not list models. Using configured model '{preferred_model}'.")
        print(e)
        return preferred_model

    if preferred_model in model_ids:
        return preferred_model

    for candidate in ["claude-haiku-4-5-20251001", "claude-sonnet-4-20250514"]:
        if candidate in model_ids:
            print(f"Configured model '{preferred_model}' not available. Falling back to '{candidate}'.")
            return candidate

    # Last resort: use the first model returned by the API
    fallback = model_ids[0] if model_ids else preferred_model
    print(f"Configured model '{preferred_model}' not available. Falling back to '{fallback}'.")
    return fallback


MODEL_A = resolve_model_name(client, MODEL_A)
MODEL_B = resolve_model_name(client, MODEL_B)


def normalize_prompt(prompt_text):
    """
    Preserve full user context for multi-turn transcripts.
    If prompt contains Human/Assistant tags, keep all turns up to
    (but not including) the final assistant turn.
    """
    if pd.isna(prompt_text):
        return ""

    text = str(prompt_text).strip()
    if not text:
        return ""

    pattern = r"(Human|Assistant):\s*(.*?)(?=\n\n(?:Human|Assistant):|\Z)"
    turns = re.findall(pattern, text, flags=re.DOTALL)

    if not turns:
        return text

    last_assistant_idx = None
    for idx in range(len(turns) - 1, -1, -1):
        if turns[idx][0] == "Assistant":
            last_assistant_idx = idx
            break

    if last_assistant_idx is None:
        return text

    prompt_turns = turns[:last_assistant_idx]
    if not prompt_turns:
        return text

    return "\n\n".join(
        f"{role}: {content.strip()}" for role, content in prompt_turns
    ).strip()


def load_prompt_dataframe(path):
    """
    Load prompts robustly.
    Falls back to line-based parsing for single-column files with unquoted commas.
    """
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not raw_lines:
        return pd.DataFrame({"prompt": []})

    if raw_lines[0].strip().lower() == "prompt":
        prompts = [line.strip() for line in raw_lines[1:] if line.strip()]
        return pd.DataFrame({"prompt": prompts})

    return pd.read_csv(path)


# Load dataset
df = load_prompt_dataframe(INPUT_FILE)

# Prefer richer context if available in enhanced file format.
source_prompt_col = "prompt_contextual" if "prompt_contextual" in df.columns else "prompt"

# 🔥 FIX: Remove empty prompts
df = df.dropna(subset=[source_prompt_col])
df["prompt_normalized"] = df[source_prompt_col].apply(normalize_prompt)
df = df[df["prompt_normalized"].str.strip().astype(bool)]

# Optional: test with small batch first
# df = df.head(10)

model_a_responses = []
model_b_responses = []

for _, row in df.iterrows():
    prompt = str(row["prompt_normalized"]).strip()

    if not prompt:
        print("Skipping empty prompt")
        model_a_responses.append("SKIPPED")
        model_b_responses.append("SKIPPED")
        continue

    try:
        # Model A response
        res_a = client.messages.create(
            model=MODEL_A,
            max_tokens=150,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Model B response
        res_b = client.messages.create(
            model=MODEL_B,
            max_tokens=150,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        model_a_responses.append(res_a.content[0].text)
        model_b_responses.append(res_b.content[0].text)

        print(f"✅ Processed: {prompt[:50]}")

    except Exception as e:
        print(f"❌ Error on prompt: {prompt}")
        print(e)
        print(f"Models used: {MODEL_A}, {MODEL_B}")
        model_a_responses.append("ERROR")
        model_b_responses.append("ERROR")

# Save output
df["model_a"] = MODEL_A
df["model_b"] = MODEL_B
df["response_model_a"] = model_a_responses
df["response_model_b"] = model_b_responses

df.to_csv(OUTPUT_FILE, index=False)

print(f"🎉 Done! Check {OUTPUT_FILE}")