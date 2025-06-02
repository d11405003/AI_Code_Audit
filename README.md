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

## 使用流程
使用python虛擬環境執行
```shell
python -m venv venv
```
下載必要套件
```shell
pip install -r requirements.txt
```
啟動fastAPI，先到project/service，執行
```shell
uvicorn api:app --reload
```
執行主程式(gradio)
```shell
python main.py
```

--- 

## 使用方式
1. 選擇 SonarQube 專案與檔案
2. 上傳規章文件
3. 顯示該檔案的錯誤資訊與原始碼
4. 點擊分析按鈕，自動產生 GPT 解釋與修正建議
5. 檢視修改後版本，綠色區塊為 GPT 建議修正內容

---

## 使用技術
- Python
- Gradio - 使用者互動介面
- LangChain + GPT-4o - 自然語言處理模型
- SonarQube / SonarCloud API - 程式碼靜態分析
- FastAPI - 提供 checklist 抽取 API
