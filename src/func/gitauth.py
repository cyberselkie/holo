import boto3
import requests
from botocore.exceptions import ClientError
from github import Auth, Github

ssm = boto3.client("ssm", region_name="us-east-2")
token = ssm.get_parameter(Name="/hologarden/client_id", WithDecryption=True)
CLIENT_ID = token["Parameter"]["Value"]
secret = ssm.get_parameter(Name="/hologarden/client_secret", WithDecryption=True)
CLIENT_SECRET = secret["Parameter"]["Value"]


def code_auth():
    r = requests.post(
        "https://github.com/login/device/code", data={"client_id": CLIENT_ID}, headers={"accept": "application/json"}
    )
    json = r.json()
    print(json)
    device_code = json["device_code"]
    user_code = json["user_code"]
    return device_code, user_code


def save_auth(refresh_token, token, uid, dynamodb=None):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden")  # type: ignore
    response = table.put_item(
        Item={"userID": str(uid), "type": "auth", "refresh_token": refresh_token, "gh_token": token}
    )
    print(response)
    print("Successfully authorized.")


def code_refresh(uid, dynamodb=None):
    g = Github()
    app = g.get_oauth_application(CLIENT_ID, CLIENT_SECRET)
    print(uid)
    try:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
        table = dynamodb.Table("hologarden")  # type: ignore
        response = table.get_item(Key={"userID": str(uid), "type": "auth"})
        print(response)
        t = response["Item"]["refresh_token"]
        token = app.refresh_access_token(t)
        update_token = table.update_item(
            Key={"userID": str(uid), "type": "auth"},
            UpdateExpression="set gh_token=:gh_token",
            ExpressionAttributeValues={":gh_token": token.token},
            ReturnValues="UPDATED_NEW",
        )
        update_refresh = table.update_item(
            Key={"userID": str(uid), "type": "auth"},
            UpdateExpression="set refresh_token=:refresh_token",
            ExpressionAttributeValues={":refresh_token": str(token.refresh_token)},
            ReturnValues="UPDATED_NEW",
        )
        print(update_token)
        print("update token")
        print(update_refresh)
        print("Token refreshed.")
    except ClientError as e:
        print(e)


def access_repo(auth, github_user, repo_name):
    g = Github(auth=auth)
    g.get_user().login
    repo = g.get_repo(f"{github_user}/{repo_name}")
    return repo


def upload_file(repo, path, commit_message, contents):
    repo.create_file(path, commit_message, contents)
    print(f"File {path} uploaded.")


def auth_login(uid):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden")  # type: ignore
    response = table.get_item(Key={"userID": str(uid), "type": "auth"})
    token = response["Item"]["gh_token"]
    auth = Auth.Token(token)
    return auth
