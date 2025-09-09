# scripts/sheet_to_csv.py
# Pull Google Sheet rows and commit to repo as data/labels.csv
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from github import Github
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--creds", default=os.environ.get("GOOGLE_CREDS_JSON", "google-creds.json"))
parser.add_argument("--out", default="data/labels.csv")
args = parser.parse_args()

GOOGLE_CREDS = args.creds
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # provided by Actions automatically
GITHUB_REPO = os.environ.get("GITHUB_REPO", os.getenv("GITHUB_REPOSITORY"))

if not GITHUB_REPO:
    raise SystemExit("GITHUB_REPO (or GITHUB_REPOSITORY) must be set")

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS, scope)
client = gspread.authorize(creds)

# Sheet name must be exactly CAi_labels
sheet = client.open("CAi_labels").sheet1
rows = sheet.get_all_records()
df = pd.DataFrame(rows)

# Ensure local folder and write local CSV file for the workflow
os.makedirs(os.path.dirname(args.out), exist_ok=True)
df.to_csv(args.out, index=False)
print(f"Wrote local csv to {args.out} (first 3 lines):")
print("\n".join(df.head(3).astype(str).values.flatten()[:10]))

# Commit to repo using PyGithub (so repo also gets updated)
csv_content = df.to_csv(index=False)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
path = args.out
try:
    contents = repo.get_contents(path)
    repo.update_file(path, "Update labels.csv from sheet", csv_content, contents.sha)
    print("Updated data/labels.csv in repo")
except Exception as e:
    repo.create_file(path, "Create labels.csv from sheet", csv_content)
    print("Created data/labels.csv in repo")
