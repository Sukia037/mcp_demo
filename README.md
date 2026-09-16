# MCP + Local RAG YZU Demo

這是一個刻意保持簡單的 CLI side project：使用者的問題由 MCP Client（MCP 用戶端）透過 `stdio` 傳給 MCP Server（MCP 伺服器），Server 再從 `data/yzu` 的元智大學資訊工程學系文件做 Retrieval（檢索），最後由 LLM（大型語言模型）根據檢索內容產生答案並保留來源。

```text
User → MCP Client → MCP Server → Local Retrieval → Retrieved Context
     → OpenAI LLM → Grounded Answer + Sources
```

目前不用 Docker、資料庫、向量資料庫或 Web UI。

## 需求

- Windows PowerShell
- Python 3.10 以上（目前以 Python 3.14 驗證）

## 第一次安裝

在專案根目錄執行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 選項 A：本機 Ollama（建議 Demo 使用）

安裝 [Ollama for Windows](https://ollama.com/download/windows) 後下載模型：

```powershell
ollama pull qwen3:8b
```

讓目前的 OpenAI-compatible client（OpenAI 相容用戶端）改連本機 API：

```powershell
$env:OPENAI_API_KEY="ollama"
$env:OPENAI_BASE_URL="http://localhost:11434/v1"
$env:OPENAI_MODEL="qwen3:8b"
```

`ollama` 是本機 API 使用的假 key，不會傳到 OpenAI。Demo 完成後可立即釋放 VRAM 或刪除約 5.2GB 的模型：

```powershell
ollama stop qwen3:8b
ollama rm qwen3:8b
```

### 選項 B：OpenAI API

設定 OpenAI API key（只存在目前的 PowerShell，不要寫進程式或 commit）：

```powershell
$env:OPENAI_API_KEY="你的 API key"
Remove-Item Env:OPENAI_BASE_URL -ErrorAction SilentlyContinue
```

雲端預設模型是 `gpt-5.4-mini`；需要時可以覆寫：

```powershell
$env:OPENAI_MODEL="gpt-5.4-mini"
```

## 啟動 Demo

預設知識庫是 `data/yzu`。若 `data` 中有其他子資料夾，可以在啟動前切換：

```powershell
$env:KNOWLEDGE_BASE="yzu"
```

例如要切換成 `data/physics`，設定 `$env:KNOWLEDGE_BASE="physics"` 後重新啟動 Client。支援的文件格式是 UTF-8 編碼的 `.txt` 與 `.md`。

互動輸入問題：

```powershell
.\.venv\Scripts\python.exe src\mcp_client.py
```

互動模式會在同一個 MCP session 中持續接受問題，並保留最近6輪使用者與助理訊息，讓使用者可以接著追問。可用指令：

```text
/history  顯示目前對話歷史
/clear    清除對話歷史並開始新主題
/help     顯示可用指令
/exit     結束對話並關閉 MCP Server
```

例如：

```text
You: 專業實習有哪些修習方式？
You: 那校外實習總共要幾學分？
```

第二題會同時帶入上一輪對話，協助 Retrieval 理解「那」指的是專業實習。對話歷史只保留在目前 CLI 執行期間，不會寫入磁碟。

或直接帶入問題：

```powershell
.\.venv\Scripts\python.exe src\mcp_client.py "資訊工程學系畢業需要多少學分？"
```

成功時會看到純文字標題、Server 狀態、`ANSWER`、`GENERATION`、`SOURCES`（來源）以及 Server 正常關閉。本機模式的 Generation 應顯示 `LLM (ollama / qwen3:8b)`。

如果 API key 未設定、網路中斷或 LLM API 暫時失敗，程式會標示 `template fallback` 並回傳最相關的原始講義內容；這只是保底模式，正常 Demo 應看到 `Generation: LLM`。

## 建議 Demo 問題

| 問題 | 預期主要來源 |
|---|---|
| `資訊工程學系畢業需要多少學分？` | `元智大學資訊工程學系必修科目表.txt` |
| `程式能力檢定要答對幾題？` | `元智大學資訊工程學系必修科目表.txt` |
| `哪些選修課程可能不會正常開課？` | `元智大學資訊工程學系選修科目表.txt` |
| `申請專業實習需要符合哪些條件？` | `元智大學資訊工程學系專業實習實施辦法.txt` |
| `專題製作期間要完成哪些活動？` | `元智大學資訊工程學系專題製作實施要點.txt` |
| `海外研習中斷後還能累計嗎？` | `元智大學資訊工程學系海外研習實施要點.txt` |

文件範圍外的問題，例如 `How do I bake a chocolate cake?`，應回答找不到足夠的本地資料，而不是自行編造。

## 一鍵 Smoke Test（冒煙測試）

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

成功時最後一行是：

```text
SMOKE TEST PASSED
```

完整單元測試：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 面試時可說明的設計

- MCP Client 負責啟動 Server、呼叫 MCP tool（MCP 工具）並顯示結果。
- Client 在同一個 MCP session 管理最近6輪對話，提供歷史查看、清除與結束指令。
- MCP Server 暴露連線檢查、文件狀態、檢索與問答四個 tools。
- Local Retrieval（本地檢索）使用可解釋的關鍵字權重，不需要外部資料庫。
- Server 使用最近一輪使用者問題協助解析追問；LLM 收到有限的對話歷史與 Retrieval 找出的 top 3 片段，prompt 要求所有事實仍須由文件支持。
- 回答永遠同時保留檢索來源；找不到相關內容時不呼叫 LLM，也不產生答案。

## 診斷命令

```powershell
.\.venv\Scripts\python.exe src\mcp_client.py --health
.\.venv\Scripts\python.exe src\mcp_client.py --knowledge-status
.\.venv\Scripts\python.exe src\mcp_client.py --search "程式能力檢定要答對幾題？"
```
