# AI 協助軟體稽核與程式碼修復系統

本系統針對 **SonarQube 掃描出的程式碼錯誤**，自動結合 GPT 模型產生錯誤說明與修正建議，並以高亮方式顯示修改內容，協助開發者快速理解與修復問題。

---

## 主要功能

- **程式碼錯誤解析**：自動擷取 SonarQube 的錯誤資訊
- **GPT 解釋與建議**：使用 GPT 模型生成錯誤說明與修正建議
- **差異高亮顯示**：原始碼與修正版本對比，變更處以綠色標示
- **規章解析模組**：支援上傳內部開發規範，自動轉換為稽核 checklist
- **錯誤檔案篩選**：支援依照專案與檔案進行精確定位與修復

---

## 專案結構
project/
│
├── main.py # Gradio 主介面
├── requirements.txt # 套件需求
├── service/
│ ├── sonarqube_report.py # SonarQube 掃描與錯誤擷取邏輯
│ ├── test0531.py # SonarCloud 來源碼擷取模組
│ └── code_fix.py # GPT 程式碼修復模組

