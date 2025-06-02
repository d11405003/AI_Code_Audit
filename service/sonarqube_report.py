import os
import base64
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from requests.auth import HTTPBasicAuth
import sys
import json
load_dotenv()  # ✅ 僅呼叫一次

# === 環境變數 ===
SONARQUBE_URL = os.getenv("SONARQUBE_URL")
SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")
SONARQUBE_ORG = os.getenv("SONARQUBE_ORG")

# === 初始化 GPT 模型 ===
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# === 呼叫 SonarQube 取得 issue ===
def get_sonar_issues(project_key: str):
    if not SONARQUBE_URL or not SONARQUBE_TOKEN:
        raise ValueError("❌ SONARQUBE_URL 或 SONARQUBE_TOKEN 未設定")

    auth = HTTPBasicAuth(SONARQUBE_TOKEN, "")
    url = f"{SONARQUBE_URL}/api/issues/search"
    params = {
        "componentKeys": project_key,
        "resolved": "false",
        "ps": 100
    }

    response = requests.get(url, auth=auth, params=params)
    if response.status_code != 200:
        raise Exception(f"SonarQube API 錯誤: {response.status_code} {response.text}")
    return response.json().get("issues", [])


# === 使用 GPT 分析掃描結果與清單比對 ===
def analyze_with_checklist(checklist: list[str], sonar_issues: list[dict]) -> tuple[str, list[tuple[str, int]]]:
    sonar_summary = "\n".join([
        f"- {issue.get('message')} (rule: {issue.get('rule')}, line: {issue.get('line')})"
        for issue in sonar_issues
    ])

    # 🔎 額外蒐集檔案與行數
    error_locations = [
        (issue.get("component", "N/A").split(":")[-1], issue.get("line", "N/A"))
        for issue in sonar_issues if issue.get("component") and issue.get("line")
    ]

    prompt = PromptTemplate.from_template("""
你是一位軟體品質分析員，請根據下列專案的靜態分析結果與稽核檢查清單，評估此專案是否符合規章，並指出不符合的項目與建議。

【稽核檢查清單】:
{checklist}

【SonarQube 掃描結果】:
{sonar_summary}

請用條列方式回報不符合的項目及原因。
""")

    full_prompt = prompt.format(
        checklist="\n".join(f"- {item}" for item in checklist),
        sonar_summary=sonar_summary
    )
    analysis = llm.invoke(full_prompt).content
    return analysis, error_locations


# === 整合函式：取得掃描結果並使用 GPT 分析 ===
def generate_audit_report(project_key: str, checklist: list[str]) -> tuple[str, list[tuple[str, int]]]:
    issues = get_sonar_issues(project_key)
    return analyze_with_checklist(checklist, issues)


# === 取得所有 SonarQube 專案 key（下拉選單用）===
def get_all_sonar_projects() -> list[str]:
    if not SONARQUBE_URL:
        return ["❌ SONARQUBE_URL 未設定"]
    if not SONARQUBE_TOKEN:
        return ["❌ SONARQUBE_TOKEN 未設定"]
    if not SONARQUBE_ORG:
        return ["❌ SONARQUBE_ORG 未設定"]

    auth = HTTPBasicAuth(SONARQUBE_TOKEN, "")
    url = f"{SONARQUBE_URL}/api/projects/search"
    params = {
        "organization": SONARQUBE_ORG,
        "ps": 100
    }

    try:
        response = requests.get(url, auth=auth, params=params)
        if response.status_code != 200:
            return [f"❌ API 錯誤 {response.status_code}: {response.text}"]

        data = response.json()
        components = data.get("components", [])
        project_keys = [project.get("key") for project in components if project.get("key")]

        return project_keys if project_keys else ["⚠️ 尚無任何專案"]
    except Exception as e:
        return [f"❌ 請求失敗：{str(e)}"]
    
def get_quality_gate_status(project_key: str) -> str:
    if not SONARQUBE_URL or not SONARQUBE_TOKEN:
        return "❌ SONARQUBE_URL 或 SONARQUBE_TOKEN 未設定"

    org = os.getenv("SONARQUBE_ORG", "your-org")
    url = f"{SONARQUBE_URL}/api/qualitygates/project_status"
    params = {"projectKey": project_key}
    auth = HTTPBasicAuth(SONARQUBE_TOKEN, "")

    try:
        response = requests.get(url, auth=auth, params=params)
        if response.status_code != 200:
            return f"❌ 查詢品質閘門失敗：{response.status_code} {response.text}"

        data = response.json()
        project_status = data.get("projectStatus", {})
        status = project_status.get("status", "UNKNOWN")
        conditions = project_status.get("conditions", [])

        # === 狀態說明 ===
        if status == "NONE":
            return (
                "⚠️ 此專案目前沒有設定任何品質閘門（Quality Gate）。\n"
                "請前往 SonarCloud 專案設定頁面選擇一個 Quality Gate，例如 `Sonar way`。\n"
                f"→ [管理品質閘門](https://sonarcloud.io/organizations/{org}/quality_gates)"
            )
        elif status == "OK":
            status_display = "✅ 品質閘門狀態：**通過**"
        elif status == "ERROR":
            status_display = "❌ 品質閘門狀態：**未通過**"
        else:
            status_display = f"⚠️ 品質閘門狀態：**{status}**（未知狀態）"

        # === 條件細節 ===
        detail_lines = [status_display, "\n條件檢查："]
        if not conditions:
            detail_lines.append("（無條件設定或尚未掃描）")
        else:
            for cond in conditions:
                metric = cond.get("metricKey", "未知項目")
                actual = cond.get("actualValue", "N/A")
                error = cond.get("errorThreshold", "N/A")
                passed = cond.get("status", "NO")
                emoji = "✅" if passed == "OK" else "❌"
                detail_lines.append(f"- `{metric}`: {actual} / 閾值: {error} → {emoji}")

        return "\n".join(detail_lines)

    except Exception as e:
        return f"❌ 請求品質閘門狀態失敗：{str(e)}"
    
# === 擷取 SonarQube 專案中的程式碼片段 ===
def get_source_files_from_project(project_key: str) -> list[str]:
    if not SONARQUBE_URL or not SONARQUBE_TOKEN:
        return ["❌ SONARQUBE_URL 或 TOKEN 未設定"]

    auth = HTTPBasicAuth(SONARQUBE_TOKEN, "")
    url = f"{SONARQUBE_URL}/api/components/tree"
    params = {
        "component": project_key,
        "ps": 500
    }

    extensions = [".py", ".java", ".js", ".ts", ".c", ".cpp", ".h", ".hpp", ".html", ".htm", ".css", ".sh", ".bash"]

    try:
        response = requests.get(url, auth=auth, params=params)
        data = response.json()
        components = data.get("components", [])
        return sorted([
            comp["path"] for comp in components
            if any(comp.get("path", "").endswith(ext) for ext in extensions)
        ])
    except Exception as e:
        return [f"❌ 無法取得檔案清單：{str(e)}"]
    




