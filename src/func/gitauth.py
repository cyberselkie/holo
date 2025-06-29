import os

import boto3
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from github import Auth, Github

load_dotenv()
CLIENT_ID = os.getenv("GH_CLIENT_ID")
CLIENT_SECRET = os.getenv("GH_CLIENT_SECRET")


def code_auth():
    r = requests.post(
        "https://github.com/login/device/code", data={"client_id": CLIENT_ID}, headers={"accept": "application/json"}
    )
    json = r.json()
    print(json)
    device_code = json["device_code"]
    user_code = json["user_code"]
    return device_code, user_code


def save_auth(refresh_token, token, uid: str):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden")  # type: ignore
    response = table.put_item(
        Item={"userID": str(uid), "type": "auth", "refresh_token": refresh_token, "gh_token": token}
    )
    print(response)
    print("Successfully authorized.")


def code_refresh(uid: str, dynamodb=None):
    g = Github()
    app = g.get_oauth_application(CLIENT_ID, CLIENT_SECRET)  # type: ignore
    print(uid)
    try:
        dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
        table = dynamodb.Table("hologarden")  # type: ignore
        response = table.get_item(Key={"userID": str(uid), "type": "auth"})
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
        print(update_refresh)
    except ClientError as e:
        print(e)


def access_repo(auth, github_user: str, repo_name: str):
    g = Github(auth=auth)
    g.get_user().login
    repo = g.get_repo(f"{github_user}/{repo_name}")
    return repo


def upload_file(repo, path: str, commit_message: str, contents: str):
    repo.create_file(path, commit_message, contents)


def auth_login(uid: str):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden")  # type: ignore
    response = table.get_item(Key={"userID": str(uid), "type": "auth"})
    token = response["Item"]["gh_token"]
    auth = Auth.Token(token)
    return auth


def auth_check(uid: str):  # check if someone has used the /start command before
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden")  # type: ignore
    response = table.get_item(Key={"userID": str(uid), "type": "auth"})
    return response["Item"]


def config_check(uid: str):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden-config")  # type: ignore
    response = table.get_item(Key={"userID": str(uid)})
    try:
        return response["Item"]
    except:
        return False

def config_retrieve(uid: str):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("hologarden-config")  # type: ignore
    response = table.get_item(Key={"userID": str(uid)})
    return response["Item"]["branch"], response["Item"]["filepath"], response["Item"]["gh_username"], response["Item"]["repository"], response["Item"]["title"]
