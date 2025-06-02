import gradio as gr
import requests
import charset_normalizer
import re
from charset_normalizer import from_bytes
from PyPDF2 import PdfReader
from collections import defaultdict
from service.sonarqube_report import (
    generate_audit_report,
    get_all_sonar_projects,
    get_quality_gate_status,
    analyze_with_checklist,
    get_source_files_from_project,
    get_sonar_issues
)
from service.code_utils import (
    format_code_html,
    format_code_diff_html,
    highlight_code_multiple,
    highlight_fix_diff
)
from service.gpt_analysis import (
    explain_issues_with_gpt,
    handle_click_gpt_fix
)
from service.sonar_service import (
    extract_issues_for_state,
    load_code_only,
    handle_click_load_code,
    handle_click_gpt_explanation
)
from service.file_parser import analyze_and_audit_file
from service.Sonar_getCode import get_sonarcloud_source_code
from langchain_openai import ChatOpenAI
from service.code_fix import fix_code_with_gpt

API_URL = "http://127.0.0.1:8000/extract_checklist"
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

def update_error_buttons(errors):
    grouped = defaultdict(list)
    for file, line in errors:
        grouped[file].append(line)
    updates = []
    files = list(grouped.keys())
    for i, btn in enumerate(error_buttons):
        if i < len(files):
            updates.append(gr.update(visible=True, value=f"📄 {files[i]} ({len(grouped[files[i]])} 錯誤)"))
        else:
            updates.append(gr.update(visible=False))
    return updates

# === Gradio UI ===
with gr.Blocks(title="規章稅核 UI", css="""
    .fixed-height {
        min-height: 100px;
    }

    .scroll-box textarea {
        height: 500px !important;
        max-height: 500px !important;
        overflow-y: auto !important;
        resize: vertical !important;
    }

    #highlighted-code {
        height: 600px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: #fafafa;
        padding: 10px;
        font-family: monospace;
        font-size: 14px;
        line-height: 1.4;
    }
    """) as demo:

    gr.Markdown("# 📋 稅核助理系統")

    with gr.Column():
        gr.Markdown("### 🔍 SonarQube 稅核分析")

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                project_key_input = gr.Dropdown(
                    label="SonarQube 專案 Key",
                    interactive=True,
                    choices=get_all_sonar_projects(),
                    elem_classes=["fixed-height"]
                )
            with gr.Column(scale=1):
                file_upload = gr.File(
                    label="上傳稅核規章 (.txt / .pdf)",
                    file_types=[".txt", ".pdf"],
                    elem_classes=["fixed-height"]
                )

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                checklist_output = gr.Textbox(
                    label="📋 稅核清單",
                    lines=25,
                    max_lines=999,
                    interactive=False,
                    show_copy_button=True,
                    elem_classes=["scroll-box"]
                )
            with gr.Column(scale=1):
                gpt_output = gr.Textbox(
                    label="🧠 GPT 分析報告",
                    lines=25,
                    max_lines=999,
                    interactive=False,
                    show_copy_button=True,
                    elem_classes=["scroll-box"]
                )
            with gr.Column(scale=1):
                quality_gate_output = gr.Textbox(
                    label="🚦 品質關門狀態",
                    lines=6,
                    interactive=False,
                    show_copy_button=True
                )

        with gr.Column(scale=2):
            gr.Markdown("### 🔍 點擊錯誤檔案載入原始碼")
            error_state = gr.State()

            current_issue_data = gr.State()
            current_file_path = gr.State()
            current_lines = gr.State()

            error_buttons = []
        with gr.Column() as error_button_zone:
            for i in range(0, 20, 5):
                with gr.Row():
                    for _ in range(5):
                        btn = gr.Button(visible=False)
                        error_buttons.append(btn)

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 載入程式碼")
                current_file_display = gr.Markdown(value="📝 目前載入：尚未選取")
                old_code = gr.HTML(label="SonarCloud 原始碼（高亮）", elem_id="highlighted-code")

            with gr.Column():
                gr.Markdown("## 修改建議")
                current_file_display = gr.Markdown(value="📝 目前載入：尚未選取")

                gpt_error_reason = gr.Textbox(
                    label="💡 GPT 解釋錯誤原因",
                    lines=25,
                    max_lines=999,
                    interactive=False,
                    visible=True,
                    show_copy_button=True,
                    elem_id="gpt_reason_box",
                    elem_classes=["scroll-box"]
                )

                gpt_fix_suggestion = gr.HTML(
                    label="🛠 GPT 修正建議",
                    visible=False,
                    elem_id="highlighted-code" 
                )

                

                with gr.Row():
                    switch_to_reason_btn = gr.Button("💡 GPT 解釋錯誤")
                    switch_to_fix_btn = gr.Button("🛠 GPT 修正建議")


            def show_gpt_error_reason(issues, file_path, lines):
                explanation_text = explain_issues_with_gpt(issues, file_path, lines)
                return gr.update(visible=True, value=explanation_text), gr.update(visible=False)

            switch_to_reason_btn.click(
                fn=show_gpt_error_reason,
                inputs=[current_issue_data, current_file_path, current_lines],
                outputs=[gpt_error_reason, gpt_fix_suggestion]
            )

            switch_to_fix_btn.click(
                fn=handle_click_gpt_fix,
                inputs=[current_issue_data, current_file_path, current_lines, project_key_input],
                outputs=[gpt_fix_suggestion]
            ).then(
                lambda: [gr.update(visible=False), gr.update(visible=True)],
                outputs=[gpt_error_reason, gpt_fix_suggestion]
            )


            file_upload.change(
                fn=analyze_and_audit_file,
                inputs=[file_upload, project_key_input],
                outputs=[checklist_output, gpt_output, quality_gate_output, error_state, gpt_error_reason]
            ).then(
                fn=update_error_buttons,
                inputs=[error_state],
                outputs=error_buttons
            )

        for i, btn in enumerate(error_buttons):
            btn.click(
                fn=handle_click_load_code,
                inputs=[gr.State(i), error_state, project_key_input],
                outputs=[current_file_display, old_code]
            ).then(
                fn=handle_click_gpt_explanation,
                inputs=[gr.State(i), error_state, project_key_input],
                outputs=[gpt_error_reason, gpt_fix_suggestion]
            ).then(
                fn=extract_issues_for_state,
                inputs=[error_state, gr.State(i), project_key_input],
                outputs=[current_issue_data, current_file_path, current_lines]
            )


if __name__ == "__main__":
    demo.launch()
