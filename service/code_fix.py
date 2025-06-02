import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()
SONARQUBE_URL = os.getenv("SONARQUBE_URL")
SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")

# === 擷取指定檔案中出錯的程式碼區塊 ===
def get_code_snippets_from_issues(project_key: str, repo_path: str):
    url = f"{SONARQUBE_URL}/api/issues/search"
    params = {"componentKeys": project_key, "resolved": "false", "ps": 100}
    auth = HTTPBasicAuth(SONARQUBE_TOKEN, "")
    
    response = requests.get(url, auth=auth, params=params)
    issues = response.json().get("issues", [])
    
    snippets = []
    for issue in issues:
        file_path = issue.get("component", "").replace(f"{project_key}:", "")
        full_path = os.path.join(repo_path, file_path)
        line = issue.get("line")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                context = lines[max(0, line-4):line+3]  # 前後 3 行作為上下文
                snippets.append({
                    "file": file_path,
                    "line": line,
                    "code": "".join(context),
                    "message": issue.get("message", ""),
                    "rule": issue.get("rule", "")
                })
        except Exception as e:
            snippets.append({
                "file": file_path,
                "line": line,
                "code": "❌ 無法讀取原始碼",
                "message": str(e),
                "rule": issue.get("rule", "")
            })

    return snippets

# === 給 GPT 修復程式碼 ===
from langchain_openai import ChatOpenAI

# Initialize the language model
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def fix_code_with_gpt(snippet: dict) -> str:
    if not snippet or not isinstance(snippet, dict):
        return "❌ snippet 格式錯誤，請提供有效的字典資料。"

    required_keys = ['message', 'rule', 'line', 'code']
    for key in required_keys:
        if key not in snippet:
            return f"❌ 缺少必要欄位：{key}"

    prompt = f"""
你是一位資深程式碼修復工程師，請根據以下錯誤訊息與程式碼內容，進行**實際修正**（包含命名錯誤、型別不一致、未使用的變數等），提供修正後的程式碼版本。

🚨 問題描述: {snippet['message']}
📜 問題規則: {snippet['rule']}
📄 原始碼（第 {snippet['line']} 行附近）:
{snippet['code']}

請直接回傳完整修正後的程式碼，並確保：
1. 有根據錯誤訊息進行實際修改
2. 命名規則錯誤需更正為 PEP8 合規命名
3. 不要留下未使用變數或錯誤語法
4. 請勿添加其他說明或註解，只回傳純程式碼
"""

    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"❌ GPT 回應失敗：{str(e)}"
