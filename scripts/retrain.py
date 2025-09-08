name: Retrain CAi

on:
  workflow_dispatch:
  push:
    paths:
      - "data/**"

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          # first install requirements if you have them
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          # install common ML / HF libs (adds safety if requirements.txt missing)
          python -m pip install --no-cache-dir transformers datasets huggingface_hub gspread oauth2client sentencepiece

      - name: Write Google credentials to file
        run: |
          echo '${{ secrets.GOOGLE_CREDS_JSON }}' > google-creds.json
          # show limited info (non-sensitive) to confirm file created
          echo "Created google-creds.json and size:"
          ls -l google-creds.json

      - name: Pull sheet -> update data/labels.csv
        env:
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          mkdir -p data
          python scripts/sheet_to_csv.py --creds google-creds.json --out data/labels.csv

      - name: Validate data file
        run: |
          echo "Data file preview (first 10 lines):"
          if [ -f data/labels.csv ]; then head -n 10 data/labels.csv || true; else echo "data/labels.csv not found"; exit 1; fi

      - name: Run retrain
        env:
          DATA_PATH: data/labels.csv
        run: |
          python scripts/retrain.py

      - name: Push model to Hugging Face
        if: success()
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          python -m pip install --no-cache-dir huggingface_hub
          python scripts/push_to_hf.py --model-dir out_model --repo "shekharbislaji/CAi-Tax-Made-Easy"
