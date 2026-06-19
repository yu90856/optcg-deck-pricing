# 上線部署（Render）

程式已可在 Render 免費部署。`deck-pricing/` 資料夾已是獨立 git repo。

## 快速部署（3 步）

### 1. 推到 GitHub

在 GitHub 建立新 repo：**https://github.com/new**

- Repository name：`optcg-deck-pricing`（或自訂）
- **不要**勾選 Add README
- 建立後在終端機執行（把 `YOUR_USER` 換成你的帳號）：

```bash
cd "/Users/viola/Desktop/OPTCG UPDATE/deck-pricing"
git remote add origin https://github.com/YOUR_USER/optcg-deck-pricing.git
git push -u origin main
```

### 2. 連接 Render

1. 前往 **https://dashboard.render.com/**，用 GitHub 登入
2. 點 **New → Blueprint**
3. 選剛才的 `optcg-deck-pricing` repo
4. 確認讀到 `render.yaml`（Free、Singapore）
5. 點 **Apply**

### 3. 取得網址

部署約 2–3 分鐘，完成後網址類似：

`https://optcg-deck-pricing.onrender.com`

---

查價時若卡拍拍回傳 403，通常是 **Render 等雲端 IP 被擋**。解法：

1. 在本機執行 `python3 build_cache.py` 更新 `data/packs/`
2. `git push` 重新部署

線上版會自動使用內建價格快取（`KAPAIPAI_CACHE_FIRST=1`）。

---

| 項目 | 說明 |
|------|------|
| 費用 | 免費，不需信用卡 |
| 休眠 | 15 分鐘無人使用會休眠，再開約等 1 分鐘 |
| 地區 | `render.yaml` 已設 Singapore |

也可執行 `./deploy-to-render.sh` 查看完整提示。

## 手動建立 Web Service（不用 Blueprint）

- **Root Directory**：留空（repo 根目錄即程式）
- **Start Command**：`python3 server.py --host 0.0.0.0 --port $PORT`
- **Instance**：Free

