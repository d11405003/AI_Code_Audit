from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
import os

# === 載入環境變數 ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("❌ 請確認 .env 檔案中有設定 OPENAI_API_KEY")

# === 設定 LLM ===
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

# === 定義狀態模型 ===
class ChecklistState(BaseModel):
    content: str
    checklist: list[str] = []

class ChecklistInput(BaseModel):
    content: str

class ChecklistOutput(BaseModel):
    checklist: list[str]

# === 規章解析節點 ===
def extract_checklist(state: ChecklistState) -> dict:
    content = state.content
    prompt = f"""
你是一位軟體稽核助理，請根據以下規章內容，列出所有需要檢查的程式碼項目。
僅需輸出檢查清單，格式如下：
- 項目1
- 項目2
...

規章內容如下：
{content}
"""
    try:
        response = llm.invoke(prompt)
        lines = response.content.strip().split("\n")
        checklist = [line.lstrip("- ").strip() for line in lines if line.strip().startswith("-")]
        return {"checklist": checklist}
    except Exception as e:
        return {"checklist": [f"❌ GPT 回應錯誤：{str(e)}"]}

# === 建立 LangGraph ===
workflow = StateGraph(state_schema=ChecklistState)
workflow.add_node("parse_regulation", RunnableLambda(extract_checklist))
workflow.set_entry_point("parse_regulation")
workflow.set_finish_point("parse_regulation")
graph = workflow.compile()

# === 建立 FastAPI App ===
app = FastAPI()

@app.post("/extract_checklist", response_model=ChecklistOutput)
async def extract_checklist_route(req: ChecklistInput):
    try:
        memory = MemorySaver()
        result = graph.invoke(
            {"content": req.content},
            config={"configurable": {"checkpoint": memory}}
        )
        return {"checklist": result["checklist"]}
    except Exception as e:
        import traceback
        return {"checklist": [f"❌ 系統錯誤：{str(e)}", traceback.format_exc()]}
