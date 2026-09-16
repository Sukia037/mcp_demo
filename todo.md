# MCP Client–Server + 本地 RAG：一晚 MVP 計畫

> Repository 現況：只有空的 `agents.md`、`readme.md`、`todo.md` 和空的 `src`，目前也不是 Git repository。因此以下以空專案規劃，現在不進行實作。

## 今晚的完成定義

執行一個 CLI（命令列介面）後，使用者能輸入問題；MCP Client（MCP 用戶端）透過 `stdio`（標準輸入輸出）呼叫 MCP Server（MCP 伺服器）；Server 從本地 `.md` / `.txt` 文件找出相關片段；Client 顯示有來源檔名的答案。Demo 不依賴 Docker、資料庫或 Web UI（網頁介面）。

## A. 建議的最小系統架構

```text
User（使用者）
  ↓ 問題
CLI Client（命令列用戶端）
  ↓ MCP over stdio（透過標準輸入輸出的 MCP 通訊）
MCP Server（MCP 伺服器）
  ↓
Simple Retriever（簡易檢索器）
  ↓
Local Documents（本地 Markdown / 文字文件）
  ↓ Retrieved Context（檢索到的上下文）
LLM（大型語言模型）
  ↓ Grounded Answer（有文件根據的答案）
Answer Builder（答案組合器）
  ↓
CLI 顯示答案與來源
```

- **CLI Client（命令列用戶端）**：接收問題、啟動 Server、呼叫 MCP tool（MCP 工具）並顯示結果；不負責搜尋文件。
- **MCP Server（MCP 伺服器）**：公開最少量的工具，協調檢索與答案回傳。
- **Simple Retriever（簡易檢索器）**：把文件按段落切成 chunks（文字片段），用簡單文字命中分數排名。第一版不用 Embedding（向量嵌入）。
- **Local Documents（本地文件）**：2～3 份短小的 `.md` / `.txt` Demo 知識，可用固定問題驗證。
- **LLM（大型語言模型）**：根據檢索到的內容完成 Generation（生成）；找不到足夠資料時不可自行編造答案。
- **Answer Builder（答案組合器）**：整理 LLM 回答與來源；API 暫時失敗時可退回模板答案，但 fallback（降級模式）不能取代正常的 LLM RAG 流程。

選擇 `stdio` 是因為不需 port（連接埠）、HTTP server（HTTP 伺服器）、CORS 或部署。純檔案和簡易文字檢索沒有資料庫或索引同步問題，也能在沒有網路或 API key（API 金鑰）時 Demo。

## B. MVP TODO（依實作順序）

### [x] Milestone 1 — Client 可以成功呼叫 MCP Server

1. **要完成什麼**：完成最小 MCP round trip（MCP 往返流程）。Client 啟動 Server、建立 `stdio` session（標準輸入輸出工作階段），呼叫固定的連線檢查工具並取得固定回覆。
2. **為什麼需要它**：先單獨證明最陌生、最容易卡住的 MCP transport（MCP 傳輸）與 process lifecycle（程序生命週期）可用，不把 MCP 與 RAG 問題混在一起查。
3. **完成後看到什麼**：終端顯示 `MCP connection OK` 後正常結束，沒有殘留的 Server process（伺服器程序）。
4. **怎麼確認成功**：連續執行三次都成功；刻意給錯 Server 路徑時，Client 顯示清楚錯誤而非無限等待。
5. **大概技術**：Python（Python 程式語言）、官方 MCP Python SDK（MCP Python 開發套件）、`stdio`（標準輸入輸出）、`asyncio`（非同步執行）。

### [x] Milestone 2 — Server 可以讀到可控的本地知識

1. **要完成什麼**：準備 2～3 份短文件；Server 啟動時讀取 `.md` / `.txt`，並能回報載入的檔名和片段數量。
2. **為什麼需要它**：先驗證資料來源與路徑，才能區分「沒有讀到資料」和「搜尋找不到」兩種錯誤。
3. **完成後看到什麼**：診斷結果顯示例如載入 3 個文件、產生 8 個 chunks（文字片段），並列出檔名。
4. **怎麼確認成功**：加入含獨特句子的文件後片段數增加；不支援的副檔名被忽略；資料目錄不存在時有清楚錯誤。
5. **大概技術**：Python 檔案讀取、Markdown（標記語言）/ plain text（純文字）、段落式 chunking（文字切塊）。

### [x] Milestone 3 — 給定問題，可以找出相關文件片段

1. **要完成什麼**：Server 的搜尋工具接收問題，對片段做簡單文字比對與排名，回傳前 3 個片段、分數和來源檔名。
2. **為什麼需要它**：這是 RAG 中 Retrieval（檢索）的核心；先讓搜尋結果可觀察，答案不對時才能判斷是檢索或組合出錯。
3. **完成後看到什麼**：標準問題的第一名是預期文件；無關問題回傳「找不到足夠相關內容」。
4. **怎麼確認成功**：為 3 個固定問題定義預期第一名來源並逐一測試；另測空問題和完全無關的問題。
5. **大概技術**：keyword matching（關鍵詞比對）、substring matching（子字串比對）、簡單文字命中分數；不用 Embedding（向量嵌入）或 vector database（向量資料庫）。

### [x] Milestone 4 — 跑通真正的端到端問答

1. **要完成什麼**：Client 接收問題並透過 MCP 呼叫 Server；Server 檢索、組合回答與來源；Client 顯示結果。此時得到第一個可 Demo 版本。
2. **為什麼需要它**：串起 User → Client → MCP Server → Retrieval → Answer，及早發現介面格式和程序關閉問題。
3. **完成後看到什麼**：CLI 顯示簡短答案、引用片段與來源檔名，內容來自本地文件。
4. **怎麼確認成功**：跑過 3 個標準問題；修改文件中的一項事實並重啟後，答案跟著改變，證明答案不是寫死的。
5. **大概技術**：MCP tool call（MCP 工具呼叫）、structured result（結構化結果）、CLI input/output（命令列輸入輸出）、template-based answer（模板式答案）。

### Checkpoint — 保存第一個可運作版本

Milestone 4 驗收成功後，先建立一次 Git commit。

此 commit 必須保存目前已能運作的：

- MCP Client
- MCP Server
- Local Document Retrieval
- End-to-end 問答流程

後續 Milestone 發生問題時，不應破壞這個已知可運作版本。

建議 commit message：

```yaml
feat: complete working MCP RAG MVP
```

---

### [x] Milestone 5 — 加上基本 Demo 錯誤處理

1. **要完成什麼**：只處理最常見的 Demo 錯誤：空問題、沒有找到相關內容、Server / LLM 錯誤，以及 Ctrl+C 正常離開。
2. **為什麼需要它**：避免常見錯誤讓現場只剩難讀的錯誤堆疊或程式明顯卡死，不在今晚追求完整錯誤系統。
3. **完成後看到什麼**：上述錯誤都顯示簡短、可讀的訊息；使用者可以理解發生什麼事並正常離開。
4. **怎麼確認成功**：分別送出空問題、無答案問題、模擬 Server / LLM 錯誤並按一次 Ctrl+C；核心 Demo 不只出現整頁 stack trace（錯誤堆疊），也不會明顯卡死。
5. **大概技術**：exception handling（例外處理）、`KeyboardInterrupt`（鍵盤中斷）、簡短錯誤訊息。

**今晚只要求：**

- 空問題
- 沒有找到相關內容
- Server / LLM 發生錯誤時顯示簡短可讀訊息
- Ctrl+C 可以正常離開

**有時間再處理，不阻擋 MVP 完成：**

- 完整 timeout handling（逾時處理）
- 各種錯誤路徑
- 完整 process cleanup（程序清理）驗證
- 大量 logging（紀錄）
- 完整錯誤測試矩陣

**完成條件：**核心 Demo 發生常見錯誤時，不會只出現整頁 stack trace，也不會讓程式明顯卡死即可。

### [x] Milestone 6 — 做成可重複的 Demo 流程

1. **要完成什麼**：補上最短安裝/執行說明、依賴清單、3～5 個標準問題與預期結果，以及一個 smoke test（冒煙測試）；從乾淨終端完整彩排。
2. **為什麼需要它**：固定步驟和驗收問題能降低現場輸錯指令或依賴環境殘留的風險。
3. **完成後看到什麼**：照 README（專案說明）複製少量指令即可啟動；smoke test 清楚顯示通過或失敗。
4. **怎麼確認成功**：關閉所有舊程序、開新終端、完全照 README 操作；連續跑兩輪標準問題，來源都符合預期。
5. **大概技術**：Python virtual environment（Python 虛擬環境）、`requirements.txt`（依賴清單）、README、簡單 smoke-test command（冒煙測試命令）。

### [x] Milestone 7 — 用 LLM 完成真正的 RAG Generation（必做）

1. **要完成什麼**：只把 Retrieval（檢索）找出的片段交給 LLM（大型語言模型），讓它主要根據這些內容回答並保留來源，完成真正的 RAG Generation（檢索增強生成）。
2. **為什麼需要它**：這是今晚 MVP 的必要功能，讓系統不只回傳片段，而是用檢索到的上下文產生有根據的答案。
3. **完成後看到什麼**：LLM 能綜合相關片段，輸出 Grounded Answer（有文件根據的答案）與來源；資料不足時明確說無法從文件回答。
4. **怎麼確認成功**：答案事實都能在引用片段找到；詢問文件沒有的內容時不自行編造；移除 API key 或模擬 API 失敗時 fallback（降級模式）仍可回傳模板答案。
5. **大概技術**：LLM API（大型語言模型介面）、prompt（提示詞）、context grounding（上下文約束）、environment variable（環境變數）。

目標流程：

```arduino
User Question
↓
MCP Client
↓
MCP Server
↓
Retrieval
↓
Retrieved Context
↓
LLM
↓
Grounded Answer
↓
Answer + Sources
```

LLM 必須主要根據 Retrieval 找出的內容回答。如果 Retrieval 找不到足夠資料，LLM 不應自行編造答案。如果 API key、網路或 LLM API 暫時失敗，可以保留 template answer（模板答案）作為 fallback，但 fallback 不能取代正常的 LLM RAG 流程。

### [x] Milestone 8 — 終端顯示美化（可刪除）

1. **要完成什麼**：只在核心穩定後，加上簡短標題、答案/來源分區或少量顏色。
2. **為什麼需要它**：提高可讀性，但不增加核心能力。
3. **完成後看到什麼**：面試官能一眼區分問題、答案、引用和錯誤。
4. **怎麼確認成功**：一般 PowerShell 顯示正常；關閉顏色後資訊仍完整。
5. **大概技術**：純文字格式；真的需要才用 Rich（Python 終端格式化套件）。**可刪除。**

## C. 建議刪掉或延後的東西

- Web UI、React（前端框架）、FastAPI（Python API 框架）。
- HTTP / SSE（伺服器推送事件）與遠端 Server；本機 `stdio` 足夠。
- Docker（容器）、雲端部署、登入、權限、多使用者、監控平台。
- PostgreSQL、MongoDB 或任何正式資料庫。
- Pinecone、Milvus、Weaviate、Chroma 等 vector database（向量資料庫）。
- LangChain、LlamaIndex 等 RAG framework（RAG 框架）；對幾份文件只會增加抽象和 Debug 成本。
- Embedding（向量嵌入）、reranker（重排序模型）、hybrid search（混合搜尋）。
- PDF、Word、圖片、OCR（光學字元辨識）；今晚只支援 `.md` / `.txt`。
- 自動監看文件、增量索引、快取、對話記憶、串流輸出。
- 多 agent（代理）、多個 MCP Server、複雜 resource / prompt 功能；只做最少 tools。
- 完整測試矩陣、效能壓測、plugin system（外掛系統）。
- 終端美化：Milestone 1～7 穩定完成後才考慮。

## 最容易卡住的地方與簡化方式

| 風險 | 原因 | 今晚的處理方式 |
|---|---|---|
| MCP SDK 版本或 API 用法 | 網路範例可能是別的版本 | 實作時以已安裝版本與官方文件為準；先完成固定回覆往返 |
| `stdio` 被一般輸出污染 | Server 的 debug 輸出可能破壞 MCP 訊息 | 協定期間只把紀錄寫到標準錯誤 |
| Client 啟動 Server 的路徑 | 從不同目錄啟動會找不到檔案 | 路徑以程式檔位置解析，不依賴目前目錄 |
| 中文或同義詞搜尋失敗 | 簡單比對不理解語意 | Demo 文件與問題使用可對上的詞；做子字串/中文片段命中，不追求通用搜尋 |
| 文件切塊品質 | 太小沒上下文，太大太吵 | 文件保持短小，優先按標題或空行分段 |
| LLM API、網路、額度、金鑰 | 外部因素不穩定 | 正常流程仍使用 LLM；模板答案只作為 API 暫時失敗時的 fallback |
| Demo 像寫死答案 | 固定輸出不能證明讀了文件 | 顯示來源；可現場改文件事實後重跑，答案應跟著變 |

## 可以先做假的或簡化的部分

- 用 2～3 份為 Demo 特別寫的短文件，不需真實大型資料集。
- 用透明的文字命中分數，只保證標準問題穩定，不宣稱語意搜尋。
- API 暫時失敗時可用模板整理真實檢索片段，但正常的完整 RAG 流程仍必須經過 LLM Generation（生成）。
- 每次 Server 啟動重新讀文件，不做持久化索引。
- 只做單輪問答，不保留聊天記憶。
- 一個主要問答 tool 加一個診斷方式即可，不展示全部 MCP 功能。

## D. 第一個 milestone：確切目標

第一步只做一件事：**讓 Python CLI Client 透過 MCP 的 `stdio` 成功呼叫本機 MCP Server，拿到固定健康檢查回覆，然後雙方乾淨結束。**

成功時應看到類似：

```text
Starting MCP server...
MCP connection OK
Server closed cleanly
```

此時不讀文件、不搜尋、不呼叫 LLM。驗收標準是連續執行三次都成功，而且結束後沒有殘留 Server process。完成後才進入 Milestone 2。

## 今晚執行優先順序

### 必做

- Milestone 1 — MCP Client ↔ Server
- Milestone 2 — 本地文件載入
- Milestone 3 — Retrieval
- Milestone 4 — End-to-end
- **Milestone 4 完成後立即 Git commit**
- Milestone 5 — 基本 Error Handling
- Milestone 6 — Demo / README
- Milestone 7 — LLM Generation

### 有時間再做

- Milestone 8 — CLI 美化

## 成功標準

**最低保底版本**

Milestone 1～4 完成，而且 Milestone 4 已 commit。

此時至少保留一個可以運作的：

```arduino
Client
→ MCP Server
→ Local Retrieval
→ Answer
```

版本。

**面試 Demo 完整版本**

Milestone 1～7 完成：

```arduino
User Question
→ MCP Client
→ MCP Server
→ Local Retrieval
→ LLM Grounded Answer
→ Answer + Sources
```

並且可以依 README 從新 terminal 啟動並完成 Demo。

**加分版本**

Milestone 8 或其他非必要改善。
