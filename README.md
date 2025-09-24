# Anime Quiz App

這個專案是一個在局域網內使用的動漫歌曲猜題遊戲。後端由 FastAPI 提供房間、玩家、答題與題庫管理，前端使用 React (Vite) 呈現主持人與玩家的互動畫面。以下以「一步一步」的方式帶你完成環境設定與基本操作。

---

## 0. 懶人包：最快的使用流程

1. **準備兩個終端機視窗**（一個跑後端、一個跑前端）。
2. **第一次使用時**請先依序執行下列指令：

   ```bash
   # 視窗 A：macOS / Linux 的後端啟動流程
   cd /你的專案路徑
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   export ADMIN_TOKEN=changeme  # 記得換成你自己的密鑰
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   ```powershell
   # 視窗 B：Windows PowerShell 中啟動前端
   cd C:\你的\專案\frontend
   npm install
   npm run dev -- --host
   ```

   > Windows 啟動虛擬環境請改用 `.venv\Scripts\Activate.ps1`，其餘指令相同；若使用 cmd，則輸入 `.venv\Scripts\activate.bat`。

3. 當後端看到 `http://0.0.0.0:8000`（或終端機顯示你的區網 IP）、前端看到 `http://127.0.0.1:5173`/`http://<你的 IP>:5173` 時就代表服務已經運作。
4. 開啟瀏覽器造訪 `http://localhost:5173`，或在其他裝置輸入 `http://<你的 IP>:5173` 加入。前端會自動改用同一台主機的 `8000` 埠作為 API 位址。

> 之後再次啟動時，只要重新執行步驟 1、5（啟動後端）與步驟 1、6（啟動前端），不需要重新安裝套件。

---

## 0.5 遊戲畫面怎麼操作？

1. 首頁輸入暱稱並建立房間；畫面會顯示要分享給朋友的房間碼。
2. 其他玩家輸入暱稱與相同房間碼加入。系統最多允許 8 名玩家，也可以只有你自己練習。
3. 房主在題庫中挑選歌曲或按「隨機播放」，題目會透過 YouTube 播放器從頭播放。
4. 歌曲播放時輸入動畫名稱作答；第一個達到 80% 相似度的人立即得 1 分並揭示正確答案。
5. 若所有玩家都按下「跳過」，這題不計分並自動換到下一首。
6. 有人達到房主設定的目標分數後，當局結束並顯示排行榜，可選擇直接開始下一局。

---

## 1. 準備環境

1. 安裝 **Python 3.11 以上**。
2. 安裝 **Node.js 18 以上**（會附帶 npm）。
3. 建議在一台電腦上執行後端與前端，其他玩家以同一個區網的瀏覽器連線即可。

---

## 2. 建立與啟用 Python 虛擬環境

在專案根目錄開啟終端機，依序輸入：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
```

看到提示字元前面多了一個 `(.venv)` 就代表虛擬環境啟用了。

---

## 3. 安裝並啟動後端 (FastAPI)

1. 安裝套件：

   ```bash
   pip install -r backend/requirements.txt
   ```

2. 設定管理者密鑰（供審核歌曲時使用，可自行替換）：

   ```bash
   export ADMIN_TOKEN=changeme  # Windows 可改用 set 或 PowerShell 的 $Env:ADMIN_TOKEN
   ```

3. （選擇性）若想改用其他資料庫，可在啟動前設定 `DATABASE_URL`；預設會在根目錄產生 `anime_quiz.db` 的 SQLite 檔。

4. 啟動伺服器：

   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   終端機出現 `Uvicorn running on http://0.0.0.0:8000`（或顯示實際區網 IP）代表後端啟動成功，其他裝置才能順利連線。

5. 測試健康檢查：在另一個終端機或瀏覽器開啟 `http://localhost:8000/health`，應會看到 `{"status":"ok"}`。

---

## 4. 安裝並啟動前端 (React / Vite)

1. **另開一個終端機視窗**，進入 `frontend/` 資料夾。
2. 安裝套件：

   ```bash
   npm install
   ```

3. 啟動開發伺服器：

   ```bash
   npm run dev -- --host
   ```

   Vite 預設會顯示「Local: http://127.0.0.1:5173」與「Network: http://<你的 IP>:5173」。

4. 在瀏覽器輸入 `http://localhost:5173`（或區網內其他裝置可用 Network URL）。若要改用不同的後端主機/埠，仍可透過 `VITE_API_BASE_URL` 環境變數覆蓋預設值。

   > 預設情況下，前端會以你目前開啟頁面所使用的主機名稱，加上 `8000` 埠作為 API 位址，因此在同一台機器啟動後端與前端時不用額外設定；若後端跑在另一台機器或不同埠才需要手動指定。

---

## 5. 基本操作流程

1. 進入首頁後，輸入暱稱並建立房間；房主會取得房間碼。
2. 其他玩家輸入相同房間碼加入，系統限制最多 8 人。
3. 房主可選擇題目或使用隨機播放開始一回合，歌曲會透過嵌入的 YouTube 播放。
4. 玩家在 2 分鐘內輸入動畫名稱作答，第一個達到 80% 相似度者得 1 分。
5. 若所有玩家都按下「跳過」，系統會自動換到下一首並不計分。
6. 達到預設或自訂的目標分數後，該局結束並顯示排行榜。

---

## 6. 題庫與後台管理

1. 只有持有 `ADMIN_TOKEN` 的使用者可以進入後台審核頁面，記得保管好這個值。
2. 在後台可以新增歌曲（輸入 YouTube 連結或影片 ID）、標記動畫名稱，並檢視待審核列表。
3. 審核通過後，歌曲才會加入正式題庫，供房主在遊戲中選用。

---

## 7. 結束服務與清理

1. 要停止後端時，在啟動伺服器的終端機按下 `Ctrl + C`。
2. 停止前端開發伺服器，也按 `Ctrl + C`。
3. 若要離開虛擬環境，在終端機輸入 `deactivate`。

---

## 8. 延伸閱讀與 API 節錄

- `POST /rooms`：建立房間並回傳房主的玩家資訊。
- `POST /rooms/{code}/join`：以暱稱加入指定房間。
- `POST /rooms/{code}/start_round`：開始下一題，可選擇指定歌曲。
- `POST /rooms/{code}/rounds/{round_id}/guess`：提交玩家猜測，伺服器回傳相似度與是否結束該題。
- `POST /rooms/{code}/rounds/{round_id}/skip`：送出跳過投票，全員同意後直接跳題。
- `GET /rooms/{code}/rounds/current`：取得目前正在播放的歌曲資訊（若題目已結束會自動顯示答案）。
- `POST /admin/songs` / `POST /admin/songs/{id}/approve` / `POST /admin/songs/{id}/reject`：題庫新增與審核（需附帶 `X-Admin-Token`）。

希望這份逐步指南能協助你順利啟動並體驗遊戲，若有更多需求可再進一步擴充功能與界面。
