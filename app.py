import os
import subprocess
from flask import Flask, request, jsonify
from utils.helpers import fetch_file_from_github, get_destination_config
import requests
import logging
import sys
app = Flask(__name__)

# Configure logging to stream to stdout (important for CF logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
app.logger.info("Flask app started")

#Health Check endpoint
@app.route("/")
def health_check():
    return "Python CF Deployer is running."

#Fetch file content from GIT repo
@app.route("/getMtarFromGIT", methods=["GET"])
def getMtarFromGIT():

    git_pat_token = os.getenv("GITHUB_PAT")
    if not git_pat_token:
        return jsonify({"error": "GitHub PAT token not found"}), 500
    # git_pat_token = request.form.get("pat_token")
    git_repo = request.form.get("repo")
    git_owner = request.form.get("owner")
    git_file_path = request.form.get("file_path")

    headers = {
        "Authorization": f"token {git_pat_token}",
        "Accept": "application/vnd.github.v3.raw"
    }
    api_url = f"https://api.github.com/repos/{git_owner}/{git_repo}/contents/{git_file_path}"
    print(f"GIT Fetch URL: {api_url}")
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == requests.codes.ok:
            file_content = response.text
            return jsonify({
                "success": True, 
                "file_content": file_content
                }),200
        else:
            return jsonify({
                "success": False, 
                "error": f"Failed to fetch file. Status: {response.status_code}",
                "details": response.text
            }), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False, 
            "error": str(e)
            }), 500
    
#Deploy mtar script to a BTP subaccount space
@app.route("/deploy", methods=["POST"])
def deploy():

    # 1) Extract form fields
    cf_org   = request.form.get("org")
    cf_space = request.form.get("space")

    git_pat_token = os.getenv("GITHUB_PAT")
    if not git_pat_token:
        return jsonify({"error": "GitHub PAT token not found"}),500
    # git_pat_token = request.form.get("pat_token")
    git_repo = request.form.get("repo")
    git_owner = request.form.get("owner")
    git_file_path = request.form.get("file_path")

    if not all([cf_org, cf_space, git_pat_token, git_repo, git_owner, git_file_path]):
        return jsonify({"error": "Missing required form fields"}), 400

#Fetch BTP Destination
    try:
        destination_name = "MTAR_DEPLOYER"
        cf_destination = get_destination_config(destination_name)
        cf_api = cf_destination["URL"]
        cf_user = cf_destination["User"]
        cf_pass = cf_destination["Password"]
        
        if not all([cf_api, cf_user, cf_pass]):
            return jsonify({"error": "Missing required form fields from destination"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get CF credentials from Destination: {str(e)}"}), 500
#Fetch mtar from GIT Repo
    try:
        mtar_file = fetch_file_from_github(git_pat_token, git_repo, git_owner, git_file_path)
    except Exception as e:
        return jsonify({"status": "failure", "error": str(e)}), 500

#Save MTAR locally
    local_filename = "uploaded.mtar"
    try:
        with open(local_filename, "wb") as f:
            f.write(mtar_file)
    except IOError as io_err:
        return jsonify({"status": "failure", "error": f"File write failed: {io_err}"}), 500
    
#Start deployment
    try:
        # 4) CF login
        login_cmd = [
            "cf", "login",
            "-a", cf_api,
            "-u", cf_user,
            "-p", cf_pass,
            "-o", cf_org,
            "-s", cf_space,
            "--skip-ssl-validation"  # only if needed
        ]
        subprocess.run(login_cmd, check=True)
        # 5) CF deploy (using the locally saved file)
        deploy_cmd = ["cf", "deploy", local_filename, "-f"]
        subprocess.run(deploy_cmd, check=True)
        return jsonify({"status": "success", "message": "MTAR deployed successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "failure",
            "error": f"cf command failed with exit code {e.returncode}",
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)