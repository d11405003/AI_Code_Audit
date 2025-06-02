import requests
import urllib.parse
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("SONARQUBE_TOKEN")

def get_sonarcloud_source_code(key: str) -> str:
    encoded_key = urllib.parse.quote(key, safe='')
    url = f"https://sonarcloud.io/api/sources/lines?key={encoded_key}"

    try:
        response = requests.get(url, auth=(TOKEN, ''))
        response.raise_for_status()
    except requests.RequestException as e:
        return f"❌ 無法取得程式碼：{e}"

    data = response.json()
    if "sources" not in data:
        return "❌ 回傳資料格式錯誤：找不到 sources 欄位"

    restored_code = []
    for line in data["sources"]:
        code_html = line.get("code", "")
        soup = BeautifulSoup(code_html, "html.parser")
        restored_code.append(soup.get_text())

    return "\n".join(restored_code)
