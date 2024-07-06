import string
from urllib.request import Request, urlopen


def download_md(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    response = urlopen(req).read()
    return response.decode()


def remove_punctuation(text):
    # Make a translator object to replace punctuation with none
    translator = str.maketrans("", "", string.punctuation)
    name = text.translate(translator)
    final = name.replace(" ", "-").lower()
    return final
