import os
import subprocess
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route("/")
def health_check():
    return "Python CF Deployer is running."
@app.route("/deploy", methods=["POST"])
def deploy():
    """
    Expects multipart/form-data:
Fields (text):
          api_url, username, password, org, space
File (binary):
          mtar (the actual .mtar file)
    Saves the uploaded mtar locally as 'uploaded.mtar'
    Then runs 'cf deploy uploaded.mtar'
    """
    # 1) Extract form fields
    cf_api   = request.form.get("api_url")
    cf_user  = request.form.get("username")
    cf_pass  = request.form.get("password")
    cf_org   = request.form.get("org")
    cf_space = request.form.get("space")
    if not all([cf_api, cf_user, cf_pass, cf_org, cf_space]):
        return jsonify({"error": "Missing required form fields"}), 400
    # 2) Check if file was provided
    if "mtar" not in request.files:
        return jsonify({"error": "No 'mtar' file provided"}), 400
    # 3) Save the uploaded file
    mtar_file = request.files["mtar"]  # <input name="mtar" ...>
    local_filename = "uploaded.mtar"
    mtar_file.save(local_filename)
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
        deploy_cmd = ["cf", "deploy", local_filename, "--yes"]
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