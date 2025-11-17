import os
import msal
from dotenv import load_dotenv

#https://kroger.atlassian.net/wiki/spaces/8451KPMME/pages/86685727/KAP+API+-+01+-+Pre-requirements+for+Product+Support#KAPAPI-01-Pre-requirementsforProductSupport-RedisReadOnlyAccess

def load_env_config():
    return {
        "stg": {
            "client_id": os.getenv("STG_REDIS_CLIENT_ID"),
            "client_secret": os.getenv("STG_REDIS_CLIENT_SECRET")
        },
        "tst": {
            "client_id": os.getenv("TST_REDIS_CLIENT_ID"),
            "client_secret": os.getenv("TST_REDIS_CLIENT_SECRET")
        },
        "dev": {
            "client_id": os.getenv("DEV_REDIS_CLIENT_ID"),
            "client_secret": os.getenv("DEV_REDIS_CLIENT_SECRET")
        },
        "prd": {
            "client_id": os.getenv("PRD_REDIS_CLIENT_ID"),
            "client_secret": os.getenv("PRD_REDIS_CLIENT_SECRET")
        }
    }

def get_access_token(env):

    config = local_redis_env_config.get(env.lower(), local_redis_env_config["dev"])
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    tenant_id = "5f9dc6bd-f38a-454a-864c-c803691193c5"
    resource_scope = "https://redis.azure.com/.default"

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = msal.ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=authority
    )

    result = app.acquire_token_for_client(scopes=[resource_scope])

    if "access_token" in result:
        access_token=result["access_token"]
        print("Access Token:", access_token)
    else:
        print("Failed to acquire token.")
        print("Error: ", result.get("error"))
        print("Error Description: ", result.get("error_description"))

# if __name__ == "__main__":
#     load_dotenv()
#     local_redis_env_config = load_env_config()
#     get_access_token(os.getenv("ENV_REDIS_LOCAL"))