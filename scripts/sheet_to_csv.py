# scripts/sheet_to_csv.py
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from github import Github

# Use fixed creds file (workflow creates this)
GOOGLE_CREDS = "google-creds.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # provided by Actions automatically
GITHUB_REPO = os.environ.get("GITHUB_REPO", os.getenv("GITHUB_REPOSITORY"))

if not GITHUB_REPO:
    raise SystemExit("GITHUB_REPO (or GITHUB_REPOSITORY) must be set")

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS, scope)
client = gspread.authorize(creds)

# Sheet name must be exactly CAi_labels
sheet = client.open("CAi_labels").sheet1
rows = sheet.get_all_records()
df = pd.DataFrame(rows)

# Ensure folder
os.makedirs("data", exist_ok=True)
csv_content = df.to_csv(index=False)

# Commit to repo using PyGithub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
path = "data/labels.csv"
try:
    contents = repo.get_contents(path)
    repo.update_file(path, "Update labels.csv from sheet", csv_content, contents.sha)
    print("Updated data/labels.csv")
except Exception:
    repo.create_file(path, "Create labels.csv from sheet", csv_content)
    print("Created data/labels.csv")
