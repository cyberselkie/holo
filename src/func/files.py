import string
from urllib.request import Request, urlopen

import requests
from github import Github

from src.func.gitauth import auth_login


def download_md(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    response = urlopen(req).read()
    return response.decode()


def remove_punctuation(text):
    # Make a translator object to replace punctuation with none
    translator = str.maketrans("", "", string.punctuation)
    name = text.translate(translator)
    final = name.replace(" ", "-")
    return final


def validate_repo(fp):
    try:
        x = fp.split("/")
        if x[1] is not None:
            pass
    except IndexError:
        return None
    else:
        return x


def retrieve_contents(uid, gh_username, repository, filepath):
    auth = auth_login(uid)
    g = Github(auth=auth)
    g.get_user().login

    try:
        repo = g.get_repo(f"{gh_username}/{repository}")
        contents = repo.get_contents(filepath)
        return contents
    except:
        return False


def download_contents(contents):
    file = contents.download_url
    r = requests.get(file)
    print(r.text)
    return r.text, contents.name
