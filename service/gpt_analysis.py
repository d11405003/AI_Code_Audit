from collections import defaultdict
import re
from langchain_openai import ChatOpenAI
from service.code_utils import format_code_diff_html

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# GPT 快取區
gpt_error_cache = {}
gpt_fix_cache = {}

def clean_unicode(text):
    return re.sub(r'[\ud800-\udfff]', '', text)

def explain_issues_with_gpt(issues: list[dict], file_path: str, lines: list[int]) -> str:
    explanations = []
    for issue in issues:
        component = issue.get("component", "")
        if not component.endswith(file_path):
            continue
        if issue.get("line") not in lines:
            continue

        msg = clean_unicode(issue.get("message", ""))
        rule = clean_unicode(issue.get("rule", ""))
        line = issue.get("line", "")
        cache_key = f"{file_path}:{line}"

        if cache_key in gpt_error_cache:
            explanation = gpt_error_cache[cache_key]
            explanations.append(f"🔧 第 {line} 行 - **{msg}**（已快取）\n{explanation}\n")
            continue

        prompt = f"""
你是一位 Python 教學助教，請用簡單易懂的方式解釋下列錯誤訊息的意思與可能的修復建議：

🔢 錯誤行數：第 {line} 行
🚨 錯誤描述：{msg}
📜 規則代碼：{rule}

請用條列方式說明。
"""
        try:
            explanation = llm.invoke(prompt).content.strip()
            gpt_error_cache[cache_key] = explanation
            explanations.append(f"🔧 第 {line} 行 - **{msg}**\n{explanation}\n")
        except Exception as e:
            explanations.append(f"❌ GPT 解釋失敗：{str(e)}")
    return "\n\n".join(explanations)


# === GPT 自動修正 ===
from service.Sonar_getCode import get_sonarcloud_source_code
from service.code_fix import fix_code_with_gpt

def handle_click_gpt_fix(issues, file_path, lines, project_key) -> str:
    cache_key = f"{project_key}:{file_path}"
    if cache_key in gpt_fix_cache:
        return gpt_fix_cache[cache_key]

    component_key = f"{project_key}:{file_path}"
    original_code = get_sonarcloud_source_code(component_key)

    target_line = lines[0]
    issue = next((i for i in issues if i.get("component", "").endswith(file_path) and i.get("line") == target_line), None)
    if not issue:
        return "❌ 找不到對應的錯誤資訊"

    snippet = {
        "file": file_path,
        "line": issue.get("line"),
        "code": original_code,
        "message": issue.get("message"),
        "rule": issue.get("rule"),
    }

    try:
        fixed_code = fix_code_with_gpt(snippet).strip()

        if fixed_code.startswith("```"):
            fixed_code = "\n".join([
                line for line in fixed_code.splitlines()
                if not line.strip().startswith("```")
            ])

        if not fixed_code or not isinstance(fixed_code, str):
            return "❌ GPT 沒有產出修正內容"

        html_code = format_code_diff_html(original_code, fixed_code)
        gpt_fix_cache[cache_key] = html_code
        return html_code
    except Exception as e:
        return f"❌ GPT 修復失敗：{str(e)}"
