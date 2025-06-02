from collections import defaultdict
from service.Sonar_getCode import get_sonarcloud_source_code
from service.gpt_analysis import explain_issues_with_gpt
from service.code_utils import highlight_code_multiple
from service.sonarqube_report import get_sonar_issues


def extract_issues_for_state(error_list, index, project_key):
    from collections import defaultdict
    from service.sonarqube_report import get_sonar_issues

    grouped = defaultdict(list)
    for file, line in error_list:
        grouped[file].append(line)
    files = list(grouped.keys())
    if index >= len(files):
        return [], "", []

    file_path = files[index]
    lines = grouped[file_path]
    return get_sonar_issues(project_key), file_path, lines



def load_code_only(project_key, file_path):
    if not project_key or not file_path.strip():
        return "❌ 請選擇專案與程式碼路徑", ""
    try:
        component_key = f"{project_key}:{file_path}"
        code = get_sonarcloud_source_code(component_key)
        return code, ""
    except Exception as e:
        return f"❌ 載入失敗：{str(e)}", ""


def handle_click_load_code(index, error_list, project_key):
    grouped = defaultdict(list)
    for file, line in error_list:
        grouped[file].append(line)
    files = list(grouped.keys())
    if index >= len(files):
        return "", "", ""
    file_path = files[index]
    lines = grouped[file_path]
    component_key = f"{project_key}:{file_path}"
    code = get_sonarcloud_source_code(component_key)
    highlighted = highlight_code_multiple(code, lines)
    return file_path, highlighted, ""


def handle_click_gpt_explanation(index, error_list, project_key):
    grouped = defaultdict(list)
    for file, line in error_list:
        grouped[file].append(line)
    files = list(grouped.keys())
    if index >= len(files):
        return "", ""

    file_path = files[index]
    lines = grouped[file_path]
    issues = get_sonar_issues(project_key)
    explanation = explain_issues_with_gpt(issues, file_path, lines)

    fix_suggestion = f"🔧 建議修正如下（模擬）：\n\n# TODO: 根據錯誤自動修正原始碼（未實作）"
    return explanation, fix_suggestion
