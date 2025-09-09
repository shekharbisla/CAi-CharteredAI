# scripts/retrain.py
# Minimal starter: reads data/labels.csv, creates tiny text2text fine-tune using t5-small
import os
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Trainer, TrainingArguments

DATA_PATH = os.environ.get("DATA_PATH", "data/labels.csv")
if not os.path.exists(DATA_PATH):
    print("No data file at", DATA_PATH)
    exit(0)

df = pd.read_csv(DATA_PATH)
if df.empty:
    print("No training rows found.")
    exit(0)

examples = []
# Build simple input-target pairs: invoice text placeholder -> field:value
# For MVP, original_value will be used; you should aggregate per-invoice later.
for _, r in df.iterrows():
    inp = f"field:{r.get('field_name','')} | text: {r.get('original_value','')}"
    tgt = f"{r.get('field_name','')}:{r.get('corrected_value','')}"
    examples.append({"input": inp, "target": tgt})

ds = Dataset.from_pandas(pd.DataFrame(examples))
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def preprocess(ex):
    enc = tokenizer(ex["input"], truncation=True, padding="max_length", max_length=256)
    targ = tokenizer(ex["target"], truncation=True, padding="max_length", max_length=64)
    enc["labels"] = targ["input_ids"]
    return enc

ds = ds.map(preprocess, remove_columns=ds.column_names)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

training_args = TrainingArguments(
    output_dir="out_model",
    num_train_epochs=1,
    per_device_train_batch_size=4,
    save_total_limit=1,
    logging_steps=10,
    fp16=False
)

trainer = Trainer(model=model, args=training_args, train_dataset=ds)
trainer.train()
trainer.save_model("out_model")
print("Saved model to out_model")
