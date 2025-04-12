import requests, os, json
from flask import current_app as app

#Helper function - fetch file from github
def fetch_file_from_github(git_pat_token, git_repo, git_owner, git_file_path):
    headers = {
        "Authorization": f"token {git_pat_token}",
        "Accept": "application/vnd.github.v3.raw"
    }
    api_url = f"https://api.github.com/repos/{git_owner}/{git_repo}/contents/{git_file_path}"
    print(f"GIT Fetch URL: {api_url}")

    # Fetch file content
    response = requests.get(api_url, headers=headers)
    if response.status_code == requests.codes.ok:
        return response.content
    else:
        raise ValueError(
        f"Failed to fetch file. Status: {response.status_code}\nDetails: {response.text}")

def get_destination_config(destination_name: str) -> dict:

    vcap_services_str = os.environ.get("VCAP_SERVICES")
    
    if not vcap_services_str:
        raise Exception("VCAP_SERVICES not found in environment.")

    vcap_services = json.loads(vcap_services_str)
    print(f"VCAP Services Response - {vcap_services}")

    # 1) Find the Destination service credentials
    if "destination" not in vcap_services:
        raise Exception("No 'destination' service binding found in VCAP_SERVICES.")
    destination_instance = vcap_services["destination"][0]  
    dest_credentials = destination_instance["credentials"]

    token_url = dest_credentials["url"] + "/oauth/token"
    destination_config_service_url = dest_credentials["uri"]  
    

    clientid = dest_credentials["clientid"]
    clientsecret = dest_credentials["clientsecret"]

    print(f"Client ID: {clientid}")
    print(f"Client Secret: {clientsecret}")

    # 2) Get OAuth token using client_credentials
    token_resp = requests.post(
        token_url,
        auth=(clientid, clientsecret),
        data={"grant_type": "client_credentials"}
    )
    if token_resp.status_code != 200:
        raise Exception(f"Failed to get token from Destination service. {token_resp.text}")
    token_data = token_resp.json()
    access_token = token_data["access_token"]

    print(f"Bearer Token: {access_token}")

    # 4) Get destination configuration
    dest_resp = requests.get(
        f"{destination_config_service_url}/destination-configuration/v1/destinations/{destination_name}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if dest_resp.status_code != 200:
        raise Exception(f"Failed to retrieve destination '{destination_name}'. {dest_resp.text}")

    dest_json = dest_resp.json()
    destination_config = dest_json.get("destinationConfiguration")
    if not destination_config:
        raise Exception(f"'destinationConfiguration' not found in response: {dest_json}")

    return destination_config