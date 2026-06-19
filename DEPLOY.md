# 上線部署（免費）

這個網站需要**後端**代理卡拍拍 API（瀏覽器無法直接跨域請求），因此不能只放 GitHub Pages，需要能跑 Python 的平台。

## 推薦：Render（免費、最省事）

| 項目 | 說明 |
|------|------|
| 費用 | $0，不需信用卡 |
| 網址 | `https://你的名稱.onrender.com` |
| 地區 | 建議選 **Singapore**（離台灣近） |
| 限制 | 15 分鐘沒人使用會休眠，下次開啟約等 1 分鐘 |

### 部署步驟

1. 把專案推到 **GitHub**
2. 前往 [render.com](https://render.com) 註冊，用 GitHub 登入
3. **New → Blueprint**，選你的 repo
4. Render 會讀取根目錄的 `render.yaml` 自動建立服務
5. 等部署完成，打開給你的 `.onrender.com` 網址

若不用 Blueprint，也可手動建立 **Web Service**：

- **Root Directory**：`deck-pricing`
- **Runtime**：Python 3
- **Build Command**：`echo ok`
- **Start Command**：`python3 server.py --host 0.0.0.0 --port $PORT`
- **Instance Type**：Free

---

## 其他免費選項

| 平台 | 適合嗎 | 備註 |
|------|--------|------|
| **Render** | ✅ 最推薦 | 現有程式幾乎不用改 |
| **Fly.io** | ✅ | 要寫 Dockerfile，免費額度有限 |
| **Railway** | △ | 每月約 $5 額度，用完要付費 |
| **Vercel / Netlify** | △ | 要把 API 改成 serverless 函式 |
| **Cloudflare Workers** | △ | 要改寫成 Worker，靜態放 Pages |
| **GitHub Pages** | ❌ | 只有靜態檔，無法代理卡拍拍 |
| **PythonAnywhere** | △ | 免費版網址、流量限制較多 |

---

## 自訂網域（選用）

Render 免費版可綁自己的網域，在服務的 **Settings → Custom Domains** 設定即可。
