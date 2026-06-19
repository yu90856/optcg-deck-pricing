#!/usr/bin/env bash
# 一鍵準備 Render 部署：初始化 git、提交、顯示推送與 Render 設定步驟
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

REPO_NAME="${1:-optcg-deck-pricing}"
GITHUB_USER="${2:-}"

echo "==> OPTCG 組牌造價 — Render 部署準備"
echo

if ! command -v git >/dev/null 2>&1; then
  echo "請先安裝 git（Xcode Command Line Tools）。"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init -b main
  echo "已建立 git repo"
fi

git add .
if git diff --cached --quiet; then
  echo "沒有新變更需要提交"
else
  GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-OPTCG Deploy}" \
  GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-deploy@local}" \
  GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-OPTCG Deploy}" \
  GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-deploy@local}" \
  git commit -m "$(cat <<'EOF'
Add OPTCG deck pricing web app for Render deployment.

EOF
)"
  echo "已提交變更"
fi

echo
echo "=========================================="
echo "  下一步：推到 GitHub"
echo "=========================================="
echo
if [[ -n "$GITHUB_USER" ]]; then
  REMOTE="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
  echo "1. 到 GitHub 建立新 repo（若尚未建立）："
  echo "   https://github.com/new"
  echo "   - Repository name: ${REPO_NAME}"
  echo "   - Public 或 Private 皆可"
  echo "   - 不要勾選 README / .gitignore（本地已有）"
  echo
  echo "2. 推送程式碼："
  echo "   git remote remove origin 2>/dev/null || true"
  echo "   git remote add origin ${REMOTE}"
  echo "   git push -u origin main"
else
  echo "1. 到 https://github.com/new 建立 repo，名稱建議：${REPO_NAME}"
  echo "   （不要勾選 Initialize with README）"
  echo
  echo "2. 在本資料夾執行（把 YOUR_USER 換成你的 GitHub 帳號）："
  echo "   git remote add origin https://github.com/YOUR_USER/${REPO_NAME}.git"
  echo "   git push -u origin main"
fi

echo
echo "=========================================="
echo "  下一步：Render 部署"
echo "=========================================="
echo
echo "1. 前往 https://dashboard.render.com/"
echo "2. 用 GitHub 登入"
echo "3. 點 New → Blueprint"
echo "4. 選剛才的 repo：${REPO_NAME}"
echo "5. 確認讀到 render.yaml，Instance 選 Free、Region 選 Singapore"
echo "6. Apply 後等 2–3 分鐘"
echo
echo "完成後網址會是：https://${REPO_NAME}.onrender.com"
echo "（若名稱被占用，Render 會加隨機字尾）"
echo
