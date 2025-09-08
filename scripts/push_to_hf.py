# scripts/push_to_hf.py
import argparse, shutil, os
from huggingface_hub import HfApi, Repository

parser = argparse.ArgumentParser()
parser.add_argument("--model-dir", required=True)
parser.add_argument("--repo", required=True)  # e.g. youruser/CAi-invoice-model
args = parser.parse_args()

api = HfApi()
# create repo if not exists (will raise if already exists)
try:
    api.create_repo(repo_id=args.repo, private=True)
except Exception as e:
    print("create_repo:", e)

local = "hf_tmp"
if os.path.exists(local):
    shutil.rmtree(local)
repo_local = Repository(local_dir=local, clone_from=f"https://huggingface.co/{args.repo}", use_auth_token=True)
# copy model
shutil.copytree(args.model_dir, os.path.join(local, "model"), dirs_exist_ok=True)
repo_local.push_to_hub(commit_message="Push model update")
print("Pushed model to HF:", args.repo)
