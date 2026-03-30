# LLM Response Eval Pipeline

Comparing two Claude models on **customer-service-style prompts**: same inputs, side-by-side responses, structured ratings, and lightweight analysis for charts and Airtable.

---

## Objective

The goal is to **measure and compare reply quality** from two different language models under the same conditions—so differences reflect model (and prompt) behavior, not different test sets. This repo supports:

1. **Curated complaint-style prompts** spanning shipping, returns, billing, accounts, and product issues.  
2. **Paired generation** (Model A vs Model B on identical prompts).  
3. **Human judgment** on **accuracy**, **helpfulness**, **conciseness**, and **tone** (1–5 each, per model), using the rubric below.  
4. **Aggregates** (win rates, averages by dimension, category breakdowns) and **exports** for visualization.

This is a **small-sample, rubric-based** evaluation: useful for iteration and demos, not a substitute for production monitoring or large human studies.

---

## Methodology

### 1. Building the prompt set

Start from a fixed pool of **short, single-turn customer scenarios** (shipping, returns, billing, accounts, product issues). The set is then **enriched in a systematic way**: each prompt gets a **topic label** and a coarse **difficulty** hint from simple keyword rules, and a **slightly richer variant** adds a minimal multi-turn frame so some evaluations see a bit more context than a bare one-liner.

### 2. Generating paired responses

For every prompt, the pipeline calls the **same cloud API** twice with **identical user content**—once for **Model A** and once for **Model B**—so comparisons are not confounded by different inputs. If a prompt is stored as a short dialogue, **normalization keeps the full customer-side context** instead of dropping everything except the last line. Outputs are stored as **side-by-side replies** plus which model ID produced each.

### 3. Human review and derived scores

Model outputs are merged into a **review-ready table** (IDs, reviewer fields, both responses). Human raters assign **independent 1–5 scores** per model on **accuracy**, **helpfulness**, **conciseness**, and **tone**, using the [evaluation guidelines](#evaluation-guidelines) (same definitions for every row). From those four dimensions, the workflow computes **which model wins the row** (or a tie) from the **mean of the four scores**, and **which single dimension had the largest gap** between models for that row.

### 4. Aggregation and reporting

The scored table is **summarized in code**: overall win mix, **means by dimension**, **breakdowns by topic category**, and frequency of **largest-gap dimensions**. Summary **charts** and **tabular exports** are produced for slides, notebooks, or tools like Airtable—without changing the underlying ratings.

---

## Models compared

| Role    | Default model ID              | Notes                          |
|---------|-------------------------------|--------------------------------|
| Model A | `claude-haiku-4-5-20251001`   | Faster / lighter default       |
| Model B | `claude-sonnet-4-20250514`    | Stronger default in the family |

Override with `ANTHROPIC_MODEL_A` and `ANTHROPIC_MODEL_B`. The generation step can **check which model IDs your API key can use** and fall back when a chosen ID is unavailable.

---

## Labeling & scoring techniques

### Human-labeled dimensions (1–5)

For **each model** (A and B), reviewers fill four columns—**accuracy**, **helpfulness**, **conciseness**, and **tone**—using the same rubric for every example:

| Dimension     | What it captures |
|---------------|------------------|
| **Accuracy**  | Factual and policy correctness; absence of fabrication |
| **Helpfulness** | How well the reply addresses the customer’s need and suggests actionable next steps |
| **Conciseness** | Directness and appropriate length relative to the question—not filler for its own sake |
| **Tone**      | Professional, empathetic, support-appropriate voice |

Definitions and anchor phrases for each level (1–5) are in [Evaluation guidelines](#evaluation-guidelines) under **Accuracy**, **Helpfulness**, **Conciseness**, and **Tone**.

### Derived fields

- **Largest-gap dimension**: among *More Accurate*, *More Helpful*, *More Concise*, *Better Tone*, record which had the **largest |A − B|** on that row.  
- **Row-level winner**: compare the **mean of accuracy, helpfulness, conciseness, and tone** for A vs B; call a **tie** when those means match within a small numerical tolerance.

### Topic metadata

**Topic category** (and **difficulty**) on the enriched prompt side come from **keyword rules**, not manual labeling—useful for slicing results, not ground truth for intent.

---

## Results (current scored sample, *n* = 100)

The tables below match the **latest summarized run** in this repository. **Summary charts** (win mix, mean scores by dimension, wins by topic category, and frequency of largest-gap dimensions) are generated by the same analysis step used for exports—regenerate them whenever the scored dataset changes.

### Overall row-level winner

| Outcome   | Count | % of rows |
|-----------|------:|----------:|
| Model A   | 42    | 42.0%     |
| Tie       | 30    | 30.0%     |
| Model B   | 28    | 28.0%     |

### Mean scores by dimension (1–5)

| Dimension    | Model A | Model B |
|--------------|--------:|--------:|
| Accuracy     | 1.94    | 1.86    |
| Helpfulness  | 4.92    | 4.82    |
| Conciseness  | 3.26    | 3.06    |
| Tone         | 3.64    | 3.36    |

### Wins by topic category

| Category           | Model A | Model B | Tie |
|--------------------|--------:|--------:|----:|
| account_access     | 5       | 2       | 4   |
| other              | 6       | 9       | 4   |
| payments_billing   | 9       | 2       | 1   |
| product_quality    | 3       | 1       | 1   |
| returns_refunds    | 9       | 5       | 10  |
| shipping_delivery  | 10      | 9       | 10  |

### Most frequent largest-gap dimensions (where A vs B differed most)

| Largest-gap label | Count |
|-------------------|------:|
| More Concise      | 39    |
| More Accurate     | 34    |
| Better Tone       | 21    |
| More Helpful      | 6     |

Regenerate summary charts and dashboard-ready exports by **running the analysis step** in the project (see **Getting started**).

---

## Conclusions (interpret with limitations)

1. **On aggregate metrics in this sample, Model A (Haiku) slightly leads Model B (Sonnet)** on mean accuracy, helpfulness, conciseness, and tone, and **wins more rows** on the four-metric composite (42% vs 28%), with **30% ties**. The margins on means are **small**—treat this as directional, not definitive proof one model is “better” in general.

2. **High helpfulness vs low accuracy** (both models ~4.8+ helpfulness but ~1.9 accuracy) suggests reviewers judged answers as **supportive and structured** but **weak on concrete facts** (e.g., no real order data)—which matches **generic LLM replies** without tool use or live systems. Any accuracy conclusion should be read in that **no-ground-truth-document** setting.

3. **Where A and B diverge most often**, the **largest-gap** label most often falls on **conciseness** and **accuracy**, then **tone**. **Helpfulness** rarely drives the largest gap—when models differ, perceived brevity and factual sharpness matter more in this rubric.

4. **Category slices are noisy** (*n* is small per bucket). The catch-all **other** topic bucket shows **more Model B wins** in this file; **returns/refunds** and **shipping_delivery** have many **ties**. Do not overfit product decisions to these counts without more data and consistent category definitions.

5. **Safety and formatting (structure)** are documented below as **optional** rubric dimensions but are **not part of the four scored columns**; conclusions about safety or layout are **out of scope** for the numeric aggregates above unless you add them to the sheet.

---

## Evaluation guidelines

Use these scales (1 = worst, 5 = best) when reviewing model answers. The **four human-rated columns** are **accuracy**, **helpfulness**, **conciseness**, and **tone**, in that order below. **Safety** and **Formatting** are optional reference scales if you want to capture them in notes or extend the sheet.

### Accuracy (1-5)

- **5:** Factually correct, no errors
- **4:** Mostly correct, minor imprecision
- **3:** Partially correct, some errors
- **2:** Mostly incorrect
- **1:** Completely wrong or fabricated

### Helpfulness (1-5)

- **5:** Directly addresses the user's need, actionable
- **4:** Addresses the need but missing minor details
- **3:** Partially helpful, significant gaps
- **2:** Minimally helpful
- **1:** Does not help at all

### Conciseness (1-5)

How directly the answer gets to the point, relative to what the customer asked—tight wording without hiding necessary detail.

- **5:** Lean and direct; no meaningful filler; length feels right for the question
- **4:** Mostly tight; minor redundancy, hedging, or generic padding
- **3:** Noticeably longer or more roundabout than needed; some repetition or tangents
- **2:** Verbose or hard to skim; the main takeaway or next steps are buried
- **1:** Extremely long or rambling; essential guidance is unclear or lost in noise

### Tone (1-5)

How appropriate, professional, and empathetic the voice is for customer support.

- **5:** Warm, respectful, and professional; clearly empathetic without being patronizing
- **4:** Professional and courteous; empathy is present but could feel slightly generic or stiff
- **3:** Mostly acceptable but uneven—sometimes flat, overly casual, or inconsistently empathetic
- **2:** Dismissive, cold, robotic, or mismatched to the customer’s emotional state
- **1:** Rude, hostile, sarcastic, or otherwise inappropriate for a support interaction

### Safety (1-5)

- **5:** Completely safe, appropriate for all audiences
- **4:** Safe with minor caveats
- **3:** Borderline — could be misused
- **2:** Contains potentially harmful content
- **1:** Clearly harmful or dangerous

### Formatting (1-5)

- **5:** Well structured, easy to read, appropriate length
- **4:** Good structure, minor issues
- **3:** Readable but could be improved
- **2:** Hard to follow, poor structure
- **1:** Unreadable or inappropriate length

### Mapping rubric to review columns

Per model (**A** and **B**), human raters use four columns aligned with the sections above:

| Column        | Rubric section |
|---------------|----------------|
| **accuracy**  | **Accuracy**   |
| **helpfulness** | **Helpfulness** |
| **conciseness** | **Conciseness** |
| **tone**      | **Tone**       |

**Safety** and **Formatting** are reference scales only here; they are **not** among the four primary columns unless you extend your evaluation sheet.

> **Note:** Older exports may still label accuracy as *correctness*; it is the same dimension as **Accuracy** above.

---

## Getting started

```bash
git clone https://github.com/sbhave123/LLMResponseEvalPipeline.git
cd LLMResponseEvalPipeline
```

Set the **Anthropic API key** in your environment (use a local secrets file and do not commit it). Install the Python dependencies your setup needs for API access, data handling, and optional plotting.

Optional analysis stack (charts and CSV exports). Install **pandas**, **matplotlib**, and **numpy**, then run the repository’s **analysis entrypoint** from the project root (the script that aggregates the scored table and writes figures plus export tables).
