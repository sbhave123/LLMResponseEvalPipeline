import pandas as pd
from pathlib import Path


CATEGORY_RULES = {
    "shipping_delivery": [
        "shipping", "ship", "delivery", "delivered", "tracking", "package", "order", "arrived", "transit", "courier"
    ],
    "returns_refunds": [
        "return", "refund", "exchange", "restocking", "receipt"
    ],
    "payments_billing": [
        "charged", "billing", "card", "payment", "invoice", "tax", "paypal", "promo"
    ],
    "account_access": [
        "account", "password", "login", "locked", "verify", "verification", "username"
    ],
    "product_quality": [
        "defective", "damaged", "broke", "quality", "warranty", "replacement", "expired"
    ],
}


def infer_category(prompt):
    text = str(prompt).lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def infer_difficulty(prompt):
    text = str(prompt).lower()
    high_risk_markers = ["fraud", "hacked", "charged twice", "denied", "suspended"]
    ambiguity_markers = ["why", "what now", "what do i do", "status", "can i still"]

    if any(marker in text for marker in high_risk_markers):
        return "hard"
    if any(marker in text for marker in ambiguity_markers):
        return "medium"
    return "easy"


def build_contextual_variant(prompt):
    prompt = str(prompt).strip()
    return (
        f"Customer: {prompt}\n\n"
        "Agent: I am sorry you are dealing with this. I can help check next steps.\n\n"
        "Customer: I already tried basic troubleshooting and still need help."
    )


def load_prompt_dataframe(path):
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not raw_lines:
        return pd.DataFrame({"prompt": []})

    if raw_lines[0].strip().lower() == "prompt":
        prompts = [line.strip() for line in raw_lines[1:] if line.strip()]
        return pd.DataFrame({"prompt": prompts})

    return pd.read_csv(path)


def main():
    df = load_prompt_dataframe("withoutGroupings_data.csv")
    df = df.dropna(subset=["prompt"]).copy()

    df["category"] = df["prompt"].apply(infer_category)
    df["difficulty"] = df["prompt"].apply(infer_difficulty)
    df["prompt_contextual"] = df["prompt"].apply(build_contextual_variant)

    df.to_csv("withoutGroupings_data_enhanced.csv", index=False)
    print(f"Saved {len(df)} rows to withoutGroupings_data_enhanced.csv")


if __name__ == "__main__":
    main()
