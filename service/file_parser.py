import requests
from PyPDF2 import PdfReader
from charset_normalizer import from_bytes
from service.sonarqube_report import generate_audit_report, get_quality_gate_status

API_URL = "http://127.0.0.1:8000/extract_checklist"

def analyze_and_audit_file(file, project_key):
    if file is None or not project_key.strip():
        return "❌ 請選擇檔案並選擇 SonarQube 專案 key", "", "", [], ""
    try:
        filename = file.name
        if filename.endswith(".txt"):
            with open(filename, "rb") as f:
                raw = f.read()
            result = from_bytes(raw)
            best_guess = result.best()
            if best_guess is None:
                return "❌ 無法解析檔案，請轉為 UTF-8 再試一次。", "", "", [], ""
            content = str(best_guess)
        elif filename.endswith(".pdf"):
            reader = PdfReader(filename)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            return "❌ 不支援的檔案格式", "", "", [], ""

        # === 呼叫 FastAPI 拿 checklist
        response = requests.post(API_URL, json={"content": content})
        if response.status_code != 200:
            return f"❌ FastAPI 錯誤 {response.status_code}: {response.text}", "", "", [], ""

        checklist = response.json().get("checklist", [])
        if not checklist:
            return "❌ FastAPI 沒有產生有效的 checklist", "", "", [], ""

        checklist_text = "\n".join(f"- {item}" for item in checklist)
        gpt_report, error_locations = generate_audit_report(project_key, checklist)
        quality_gate_status = get_quality_gate_status(project_key)

        return checklist_text, gpt_report, quality_gate_status, error_locations, ""
    except Exception as e:
        return f"❌ 分析失敗：{str(e)}", "", "", [], ""
