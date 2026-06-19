const deckInput = document.getElementById("deck-input");
const priceBtn = document.getElementById("price-btn");
const pasteBtn = document.getElementById("paste-btn");
const clearBtn = document.getElementById("clear-btn");
const exportBtn = document.getElementById("export-btn");
const fileInput = document.getElementById("file-input");
const modeSelect = document.getElementById("price-mode");
const basisSelect = document.getElementById("price-basis");
const sortSelect = document.getElementById("sort-mode");
const statusEl = document.getElementById("status");
const cardList = document.getElementById("card-list");
const totalPriceEl = document.getElementById("total-price");
const totalCardsEl = document.getElementById("total-cards");
const uniqueCardsEl = document.getElementById("unique-cards");

let lastResult = null;

function formatTwd(n) {
  if (n == null) return "—";
  return `NT$ ${Number(n).toLocaleString("zh-TW")}`;
}

function setStatus(text, type = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${type}`.trim();
}

function sortCards(cards, mode) {
  const list = [...cards];
  if (mode === "id") {
    return list.sort((a, b) => a.cardId.localeCompare(b.cardId));
  }
  return list.sort((a, b) => {
    const av = a.lineTotal ?? -1;
    const bv = b.lineTotal ?? -1;
    if (bv !== av) return bv - av;
    return a.cardId.localeCompare(b.cardId);
  });
}

function renderCards(data) {
  if (!data.cards?.length) {
    cardList.innerHTML = `<div class="empty">沒有可顯示的卡牌</div>`;
    exportBtn.disabled = true;
    return;
  }

  const cards = sortCards(data.cards, sortSelect.value);
  cardList.innerHTML = cards
    .map((card) => {
      const missing = card.status === "missing";
      const img = card.imageUrl
        ? `<img src="${card.imageUrl}" alt="${card.cardId}" loading="lazy" onerror="this.style.visibility='hidden'">`
        : `<div class="img-placeholder"></div>`;
      const basisNote =
        !missing && card.priceSource === "lowest_fallback"
          ? '<span class="tag warn">無均價，改以最低價</span>'
          : "";
      const refPrice =
        !missing && data.price_basis === "average"
          ? `<div class="ref">最低 ${formatTwd(card.lowestPrice)}</div>`
          : !missing && data.price_basis === "lowest"
            ? `<div class="ref">均價 ${formatTwd(card.averagePrice || null)}</div>`
            : "";
      const unit = missing
        ? `<div class="line missing-text">找不到</div>`
        : `<div class="unit">${card.quantity} × ${formatTwd(card.unitPrice)}</div>
           <div class="line">${formatTwd(card.lineTotal)}</div>
           ${refPrice}${basisNote}`;
      return `
        <article class="card-row ${missing ? "missing" : ""}">
          ${img}
          <div class="card-meta">
            <div class="id">${card.cardId} × ${card.quantity}</div>
            <div class="name">${card.cardName || "（未知卡名）"}</div>
            <div class="sub">${card.rare || card.message || ""}</div>
          </div>
          <div class="card-price">
            ${unit}
            <a href="${card.kapaipaiUrl}" target="_blank" rel="noopener">卡拍拍 ↗</a>
          </div>
        </article>`;
    })
    .join("");
  exportBtn.disabled = false;
}

function exportCsv() {
  if (!lastResult?.cards?.length) return;
  const basis =
    lastResult.price_basis === "lowest" ? "最低掛單價" : "市場均價";
  const rows = [
    [
      "編號",
      "數量",
      "卡名",
      "稀有度",
      "單價",
      "小計",
      "市場均價",
      "最低掛單",
      "卡拍拍連結",
    ],
  ];
  for (const c of sortCards(lastResult.cards, sortSelect.value)) {
    rows.push([
      c.cardId,
      c.quantity,
      c.cardName || "",
      c.rare || "",
      c.unitPrice ?? "",
      c.lineTotal ?? "",
      c.averagePrice || "",
      c.lowestPrice || "",
      c.kapaipaiUrl,
    ]);
  }
  rows.push([]);
  rows.push(["預估總價", lastResult.total_price, `基準:${basis}`]);
  const csv = rows
    .map((row) =>
      row
        .map((cell) => `"${String(cell).replace(/"/g, '""')}"`)
        .join(","),
    )
    .join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `optcg-deck-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function priceDeck() {
  const deck = deckInput.value.trim();
  if (!deck) {
    setStatus("請先貼上或匯入牌組", "error");
    return;
  }

  priceBtn.disabled = true;
  exportBtn.disabled = true;
  cardList.innerHTML = `<div class="empty loading">正在向卡拍拍查價…</div>`;
  setStatus("首次查詢會下載卡表，請稍候…", "loading");

  try {
    const res = await fetch("/api/price-deck", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        deck,
        mode: modeSelect.value,
        basis: basisSelect.value,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "查價失敗");
    }
    if (data.error) {
      setStatus(data.error, "error");
      cardList.innerHTML = `<div class="empty">無法解析牌組</div>`;
      return;
    }

    lastResult = data;
    totalPriceEl.textContent = formatTwd(data.total_price);
    totalCardsEl.textContent = String(data.total_cards);
    uniqueCardsEl.textContent = String(data.unique_cards);

    const variantLabel =
      data.price_mode === "cheapest" ? "全版本最便宜" : "標準版（非異圖）";
    const basisLabel =
      data.price_basis === "lowest" ? "最低掛單價" : "市場均價";
    const miss = data.missing_cards
      ? `，${data.missing_cards} 張找不到`
      : "";
    const fallback = data.cards.filter(
      (c) => c.priceSource === "lowest_fallback",
    ).length;
    const fallbackNote = fallback ? `，${fallback} 張無均價改以最低價估算` : "";
    setStatus(
      `「${variantLabel}」×「${basisLabel}」，共 ${data.priced_cards} 張有報價${miss}${fallbackNote}`,
    );
    renderCards(data);
  } catch (err) {
    setStatus(err.message || "查價失敗", "error");
    cardList.innerHTML = `<div class="empty">查價失敗，請稍後再試</div>`;
  } finally {
    priceBtn.disabled = false;
  }
}

priceBtn.addEventListener("click", priceDeck);
pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (!text.trim()) {
      setStatus("剪貼簿是空的", "error");
      return;
    }
    deckInput.value = text.trim();
    setStatus("已貼上牌組");
  } catch {
    setStatus("無法讀取剪貼簿，請手動貼上", "error");
  }
});
clearBtn.addEventListener("click", () => {
  deckInput.value = "";
  lastResult = null;
  setStatus("");
  cardList.innerHTML = `<div class="empty">貼上 OPTCG SIM 牌組後按「查詢造價」</div>`;
  totalPriceEl.textContent = "—";
  totalCardsEl.textContent = "—";
  uniqueCardsEl.textContent = "—";
  exportBtn.disabled = true;
});
exportBtn.addEventListener("click", exportCsv);
sortSelect.addEventListener("change", () => {
  if (lastResult) renderCards(lastResult);
});

fileInput.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  deckInput.value = await file.text();
  setStatus(`已載入 ${file.name}`);
  e.target.value = "";
});

deckInput.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    priceDeck();
  }
});

if (location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
  const badge = document.getElementById("env-badge");
  if (badge) badge.textContent = "線上版";
}
