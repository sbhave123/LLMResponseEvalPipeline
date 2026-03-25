import pandas as pd

df = pd.read_csv("prompts_responses.csv")

# The dataset has 'chosen' and 'rejected' columns
# We'll use 'chosen' as our response to evaluate
df_clean = pd.DataFrame()
df_clean['ID'] = range(1, len(df) + 1)
df_clean['Prompt'] = df['chosen'].str.extract(r'Human: (.*?)\n\nAssistant:', expand=False)
df_clean['Response'] = df['chosen'].str.extract(r'Assistant: (.*?)$', expand=False)
df_clean['Category'] = 'Unassigned'
df_clean['Accuracy Score'] = ''
df_clean['Helpfulness Score'] = ''
df_clean['Safety Score'] = ''
df_clean['Formatting Score'] = ''
df_clean['Reviewer Notes'] = ''
df_clean['Reviewer Name'] = ''

# Drop any rows where extraction failed
df_clean = df_clean.dropna(subset=['Prompt', 'Response'])
df_clean = df_clean.head(100)

df_clean.to_csv("clean_prompts.csv", index=False)
print(f"Cleaned {len(df_clean)} rows successfully")