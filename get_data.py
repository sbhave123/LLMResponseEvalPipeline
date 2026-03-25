from datasets import load_dataset
import pandas as pd

# Load the dataset
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

# Convert to pandas dataframe
df = pd.DataFrame(dataset)

# Take first 100 rows
df = df.head(100)

# Save to CSV
df.to_csv("prompts_responses.csv", index=False)

print("Done! Check prompts_responses.csv")
