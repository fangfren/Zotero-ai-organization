(function () {
  "use strict";

  const state = {
    categories: [],
    items: [],
    currentItem: null,
  };

  function init() {
    const data = typeof DATA !== "undefined" ? DATA : {};
    state.items = Array.isArray(data.items) ? data.items : [];
    state.categories = Array.isArray(data.categories)
      ? data.categories
      : [];
    injectAppBar();
    wrapOpenDetail();
    bindTimers();
  }

  function injectAppBar() {
    const bar = document.createElement("div");
    bar.id = "app-bar";
    bar.innerHTML = `
      <button class="app-action primary" id="app-sync" type="button">同步数据</button>
      <button class="app-action" id="app-categories" type="button">分类管理</button>
      <button class="app-action" id="app-report" type="button">AI 报告</button>
      <button class="app-action" id="app-ai" type="button">AI 设置</button>
    `;
    document.body.appendChild(bar);

    const modal = document.createElement("dialog");
    modal.id = "app-modal";
    document.body.appendChild(modal);

    const toast = document.createElement("div");
    toast.id = "app-toast";
    document.body.appendChild(toast);

    document.querySelector("#app-sync").addEventListener("click", syncNow);
    document
      .querySelector("#app-categories")
      .addEventListener("click", openCategoriesModal);
    document
      .querySelector("#app-report")
      .addEventListener("click", openReportModal);
    document.querySelector("#app-ai").addEventListener("click", openAiModal);
  }

  function wrapOpenDetail() {
    const original = window.openDetail;
    if (typeof original !== "function") return;
    window.openDetail = function (item) {
      original(item);
      const body = document.querySelector("#detail-body");
      if (!body) return;
      const actionList = body.querySelector(".detail-actions");
      const button = document.createElement("button");
      button.className = "action-link";
      button.type = "button";
      button.textContent = "整理笔记与分类";
      button.addEventListener("click", () => openItemEdit(item));
      actionList?.appendChild(button);
    };
  }

  function bindTimers() {
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") hideModal();
    });
  }

  function showModal(html) {
    const modal = document.querySelector("#app-modal");
    modal.innerHTML = html;
    if (!modal.open) modal.showModal();
    modal.querySelector("#app-modal-close")?.addEventListener("click", hideModal);
  }

  function hideModal() {
    const modal = document.querySelector("#app-modal");
    if (modal?.open) modal.close();
  }

  function toast(message) {
    const element = document.querySelector("#app-toast");
    element.textContent = message;
    element.classList.add("visible");
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => {
      element.classList.remove("visible");
    }, 3200);
  }

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.message || `请求失败：${response.status}`);
    }
    return payload;
  }

  async function syncNow() {
    toast("正在同步 Zotero 数据…");
    try {
      await fetchJson("/api/sync", { method: "POST" });
      location.reload();
    } catch (error) {
      toast(error.message);
    }
  }

  function modalShell(title, body, footer = "") {
    return `
      <div class="app-panel" role="dialog" aria-modal="true" aria-label="${String(title).replaceAll('"', "&quot;")}">
        <div class="app-panel-header">
          <h2>${escapeHtml(title)}</h2>
          <button class="app-panel-close" id="app-modal-close" type="button" aria-label="关闭">×</button>
        </div>
        <div class="app-panel-body">${body}</div>
        ${footer ? `<div class="app-panel-footer">${footer}</div>` : ""}
      </div>
    `;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function loadCategoryConfig() {
    const payload = await fetchJson("/api/categories");
    return payload;
  }

  async function openCategoriesModal() {
    let config;
    try {
      config = await loadCategoryConfig();
    } catch (error) {
      toast(error.message);
      return;
    }
    if (config.source_mode === "zotero") {
      const zoteroCategories = config.categories.filter(
        (category) => category.source === "zotero"
      );
      const localCategories = config.categories.filter(
        (category) => category.source !== "zotero"
      );
      const zoteroCards = zoteroCategories
        .map((category) => {
          const items = state.items.filter((item) =>
            (item.categoryIds || []).includes(category.id)
          );
          return `
            <div class="category-static" style="--category-color:${escapeHtml(category.color)}">
              <span class="category-dot"></span>
              <h3>${escapeHtml(category.name)}</h3>
              <span class="status-pill">${items.length} 篇文献</span>
              <p>${escapeHtml(items.slice(0, 4).map((item) => item.title).join("、"))}</p>
            </div>
          `;
        })
        .join("");
      const localRows = localCategories
        .map(
          (category) => `
            <div class="category-row" data-category-id="${escapeHtml(category.id)}">
              <div class="app-field">
                <label>分类名称</label>
                <input type="text" data-field="name" value="${escapeHtml(category.name)}">
              </div>
              <div class="app-field">
                <label>说明</label>
                <input type="text" data-field="description" value="${escapeHtml(category.description || "")}">
              </div>
              <div class="app-field category-color">
                <label>颜色</label>
                <input type="color" data-field="color" value="${escapeHtml(category.color || "#6b7280")}">
              </div>
              <div class="app-field">
                <label>关键词</label>
                <input type="text" data-field="keywords" value="${escapeHtml((category.keywords || []).join(", "))}" placeholder="用逗号分隔">
              </div>
              <button class="category-remove" type="button" data-remove>删除</button>
            </div>
          `
        )
        .join("");
      const body = `
        <p class="report-output">Zotero 集合为只读来源，请在 Zotero 中调整集合归属；本地规则可在这里继续管理。</p>
        <div class="category-static-grid">${zoteroCards || '<p class="report-output">暂无 Zotero 集合。</p>'}</div>
        <h3 class="category-section-title">本地规则</h3>
        <div class="category-list" id="category-list-app">${localRows || '<p class="report-output">暂无本地规则。</p>'}</div>
      `;
      const footer = `
        <button class="app-action" id="category-add" type="button">新增本地规则</button>
        <button class="app-action primary" id="category-save" type="button">保存本地规则</button>
      `;
      showModal(modalShell("分类管理", body, footer));
      installCategoryEditor(config);
      return;
    }
    const rows = config.categories
      .map(
        (category) => `
          <div class="category-row" data-category-id="${escapeHtml(category.id)}">
            <div class="app-field">
              <label>分类名称</label>
              <input type="text" data-field="name" value="${escapeHtml(category.name)}">
            </div>
            <div class="app-field">
              <label>说明</label>
              <input type="text" data-field="description" value="${escapeHtml(category.description || "")}">
            </div>
            <div class="app-field category-color">
              <label>颜色</label>
              <input type="color" data-field="color" value="${escapeHtml(category.color || "#6b7280")}">
            </div>
            <div class="app-field">
              <label>关键词</label>
              <input type="text" data-field="keywords" value="${escapeHtml((category.keywords || []).join(", "))}" placeholder="用逗号分隔">
            </div>
            <button class="category-remove" type="button" data-remove>删除</button>
          </div>
        `
      )
      .join("");

    const body = `
      <div class="category-list" id="category-list-app">${rows || '<p class="report-output">尚无分类。</p>'}</div>
    `;
    const footer = `
      <button class="app-action" id="category-add" type="button">新增分类</button>
      <button class="app-action primary" id="category-save" type="button">保存分类</button>
    `;
    showModal(modalShell("分类管理", body, footer));
    installCategoryEditor(config);
  }

  function installCategoryEditor(config) {
    document
      .querySelector("#category-list-app")
      .addEventListener("click", (event) => {
        const button = event.target.closest("[data-remove]");
        if (button) button.closest(".category-row").remove();
      });
    document.querySelector("#category-add").addEventListener("click", () => {
      const suffix = Date.now().toString(36);
      const row = document.createElement("div");
      row.className = "category-row";
      row.dataset.categoryId = `category-${suffix}`;
      row.innerHTML = `
        <div class="app-field"><label>分类名称</label><input type="text" data-field="name" value="新分类"></div>
        <div class="app-field"><label>说明</label><input type="text" data-field="description" value=""></div>
        <div class="app-field category-color"><label>颜色</label><input type="color" data-field="color" value="#5b7f9a"></div>
        <div class="app-field"><label>关键词</label><input type="text" data-field="keywords" value=""></div>
        <button class="category-remove" type="button" data-remove>删除</button>
      `;
      document.querySelector("#category-list-app").appendChild(row);
    });
    document.querySelector("#category-save").addEventListener("click", async () => {
      const rows = [...document.querySelectorAll("#category-list-app .category-row")];
      const categoryById = Object.fromEntries(
        config.categories.map((category) => [category.id, category])
      );
      const categories = rows.map((row) => {
        const existing = categoryById[row.dataset.categoryId] || {};
        const value = (field) =>
          (row.querySelector(`[data-field="${field}"]`).value || "").trim();
        const keywords = value("keywords")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
        return {
          id: row.dataset.categoryId,
          name: value("name") || row.dataset.categoryId,
          description: value("description"),
          color: value("color") || "#6b7280",
          keywords,
          item_ids: Array.isArray(existing.item_ids) ? existing.item_ids : [],
          item_keys: Array.isArray(existing.item_keys) ? existing.item_keys : [],
        };
      });
      try {
        const payload = await fetchJson("/api/categories", {
          method: "PUT",
          body: JSON.stringify({
            default_category_id: config.default_category_id,
            categories,
          }),
        });
        toast(payload.message || "分类已保存。");
        setTimeout(() => location.reload(), 800);
      } catch (error) {
        toast(error.message);
      }
    });
  }

  async function openItemEdit(item) {
    let notePayload;
    let categoryConfig;
    try {
      [notePayload, categoryConfig] = await Promise.all([
        fetchJson(`/api/note/${item.id}`),
        loadCategoryConfig(),
      ]);
    } catch (error) {
      toast(error.message);
      return;
    }
    const manual = notePayload.manual || {};
    const currentIds = item.categoryIds || [];
    const zoteroManaged = categoryConfig.source_mode === "zotero";
    const categoryOptions = categoryConfig.categories
      .map(
        (category) => `
          <label>
            <input type="checkbox" data-category="${escapeHtml(category.id)}" ${currentIds.includes(category.id) ? "checked" : ""}>
            <span>${escapeHtml(category.name)}</span>
          </label>
        `
      )
      .join("");
    const zoteroNames = currentIds
      .map((id) => categoryConfig.categories.find((category) => category.id === id)?.name)
      .filter(Boolean)
      .join("、");
    const categorySection = zoteroManaged
      ? `
        <div class="app-field">
          <label>文献分类</label>
          <div class="checkbox-grid">
            <span class="status-pill">Zotero：${escapeHtml(zoteroNames || "未分类")}</span>
          </div>
        </div>
      `
      : `
        <div class="app-field">
          <label>文献分类</label>
          <div class="checkbox-grid" id="item-categories">${categoryOptions}</div>
        </div>
      `;
    const body = `
      ${categorySection}
      <div class="app-note-form" style="margin-top:16px">
        <div class="app-field">
          <label>我的理解</label>
          <textarea id="manual-understanding" placeholder="用自己的话解释这篇文献解决的问题。">${escapeHtml(manual.understanding || "")}</textarea>
        </div>
        <div class="app-field">
          <label>关键结论</label>
          <textarea id="manual-conclusions" placeholder="只记录你能够复述并判断依据的结论。">${escapeHtml(manual.conclusions || "")}</textarea>
        </div>
        <div class="app-field">
          <label>疑问</label>
          <textarea id="manual-questions" placeholder="记录没有看懂的地方。">${escapeHtml(manual.questions || "")}</textarea>
        </div>
        <div class="app-field">
          <label>与研究方向的关系</label>
          <textarea id="manual-relevance" placeholder="记录对 DFB 可靠性或光电测试的意义。">${escapeHtml(manual.relevance || "")}</textarea>
        </div>
      </div>
    `;
    const footer = `
      <button class="app-action primary" id="item-save" type="button">保存</button>
    `;
    showModal(modalShell(`整理笔记 · ${item.title}`, body, footer));
    document.querySelector("#item-save").addEventListener("click", async () => {
      const manualPayload = {
        understanding: document.querySelector("#manual-understanding").value,
        conclusions: document.querySelector("#manual-conclusions").value,
        questions: document.querySelector("#manual-questions").value,
        relevance: document.querySelector("#manual-relevance").value,
      };
      const selected = [
        ...document.querySelectorAll('#item-categories input[type="checkbox"]:checked'),
      ].map((input) => input.dataset.category);
      try {
        await fetchJson(`/api/note/${item.id}`, {
          method: "PUT",
          body: JSON.stringify({ manual: manualPayload }),
        });
        if (!zoteroManaged) {
          await fetchJson(`/api/items/${item.id}/categories`, {
            method: "PUT",
            body: JSON.stringify({ category_ids: selected }),
          });
        }
        toast(zoteroManaged ? "笔记已保存。" : "笔记和分类已保存。");
        setTimeout(() => location.reload(), 700);
      } catch (error) {
        toast(error.message);
      }
    });
  }

  async function openReportModal() {
    let aiConfig = null;
    try {
      aiConfig = await fetchJson("/api/ai/config");
    } catch (error) {
      toast(error.message);
    }
    const providerLabel = aiConfig?.provider === "codex" ? "Codex 本地" : "API";
    const providerStatus =
      aiConfig?.provider === "codex"
        ? aiConfig.codex_available
          ? "Codex 可用"
          : "Codex 未找到"
        : aiConfig?.configured
          ? "API 已配置"
          : "API 未配置";
    const options = state.items
      .map(
        (item) =>
          `<option value="${item.id}">${escapeHtml(item.title)}</option>`
      )
      .join("");
    const body = `
      <div class="status-row">
        <span class="status-pill">${escapeHtml(providerLabel)}</span>
        <span class="status-pill">${escapeHtml(providerStatus)}</span>
      </div>
      <div class="app-grid">
        <div class="app-field">
          <label>报告范围</label>
          <select id="report-scope">
            <option value="all">全部文献</option>
            <option value="item">单篇文献</option>
          </select>
        </div>
        <div class="app-field" id="report-item-field">
          <label>文献</label>
          <select id="report-item">${options}</select>
        </div>
        <div class="app-field full">
          <label>AI 改进要求</label>
          <textarea id="report-instruction" placeholder="例如：按 DFB 可靠性研究方向整理，区分原理、测量方法和挑战。"></textarea>
        </div>
        <div class="full" id="report-result"></div>
      </div>
    `;
    const footer = `
      <button class="app-action" id="report-export" type="button">导出 Markdown</button>
      <button class="app-action primary" id="report-generate" type="button">生成报告</button>
    `;
    showModal(modalShell("AI 报告", body, footer));
    const scope = document.querySelector("#report-scope");
    const itemField = document.querySelector("#report-item-field");
    scope.addEventListener("change", () => {
      itemField.style.display = scope.value === "item" ? "" : "none";
    });
    itemField.style.display = "none";

    const selectedIds = () => {
      if (scope.value === "item") {
        return [Number(document.querySelector("#report-item").value)];
      }
      return null;
    };
    const instruction = () =>
      document.querySelector("#report-instruction").value.trim();
    document
      .querySelector("#report-generate")
      .addEventListener("click", async () => {
        document.querySelector("#report-result").innerHTML =
          '<p class="report-output">正在生成报告…</p>';
        try {
          const payload = await fetchJson("/api/ai/report", {
            method: "POST",
            body: JSON.stringify({
              item_ids: selectedIds(),
              instruction: instruction(),
            }),
          });
          document.querySelector("#report-result").innerHTML = `
            <p class="status-pill">${escapeHtml(payload.message || "")}</p>
            <pre class="report-output">${escapeHtml(payload.report || "")}</pre>
          `;
        } catch (error) {
          document.querySelector("#report-result").innerHTML =
            `<p class="report-output">${escapeHtml(error.message)}</p>`;
        }
      });
    document
      .querySelector("#report-export")
      .addEventListener("click", async () => {
        try {
          const payload = await fetchJson("/api/report/export", {
            method: "POST",
            body: JSON.stringify({
              item_ids: selectedIds(),
              instruction: instruction(),
            }),
          });
          toast(payload.message + " " + payload.path);
        } catch (error) {
          toast(error.message);
        }
      });
  }

  async function openAiModal() {
    let config;
    try {
      config = await fetchJson("/api/ai/config");
    } catch (error) {
      toast(error.message);
      return;
    }
    const body = `
      <div class="status-row">
        <span class="status-pill">${config.provider === "codex" ? "Codex 本地" : "API"}</span>
        <span class="status-pill">${config.codex_available ? "Codex 可用" : "Codex 未找到"}</span>
        <span class="status-pill">${config.has_key ? "已有 API 密钥" : "无 API 密钥"}</span>
        ${config.api_key_env ? '<span class="status-pill">使用环境变量密钥</span>' : ""}
      </div>
      <div class="app-grid">
        <div class="app-field full">
          <label>报告生成方式</label>
          <select id="ai-provider">
            <option value="codex" ${config.provider === "codex" ? "selected" : ""}>Codex 本地生成</option>
            <option value="api" ${config.provider === "api" ? "selected" : ""}>OpenAI 兼容 API</option>
          </select>
        </div>
        <div class="app-field full" id="api-fields" ${config.provider === "codex" ? 'style="display:none"' : ""}>
          <div class="app-grid">
            <div class="app-field full">
              <label>OpenAI 兼容接口地址</label>
              <input type="url" id="ai-base-url" value="${escapeHtml(config.base_url)}">
            </div>
            <div class="app-field full">
              <label>模型名称</label>
              <input type="text" id="ai-model" value="${escapeHtml(config.model)}" placeholder="例如 gpt-4.1-mini">
            </div>
            <div class="app-field full">
              <label>API 密钥</label>
              <input type="password" id="ai-key" value="" placeholder="留空则保留当前密钥">
            </div>
          </div>
        </div>
      </div>
    `;
    const footer = `
      <button class="app-action primary" id="ai-save" type="button">保存设置</button>
    `;
    showModal(modalShell("AI 设置", body, footer));
    const providerSelect = document.querySelector("#ai-provider");
    const apiFields = document.querySelector("#api-fields");
    providerSelect.addEventListener("change", () => {
      apiFields.style.display = providerSelect.value === "api" ? "" : "none";
    });
    document.querySelector("#ai-save").addEventListener("click", async () => {
      const payload = { provider: providerSelect.value };
      if (providerSelect.value === "api") {
        payload.base_url = document.querySelector("#ai-base-url").value.trim();
        payload.model = document.querySelector("#ai-model").value.trim();
        const key = document.querySelector("#ai-key").value.trim();
        if (key) payload.api_key = key;
      }
      try {
        const result = await fetchJson("/api/ai/config", {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        toast(result.message || "AI 设置已保存。");
        setTimeout(() => location.reload(), 700);
      } catch (error) {
        toast(error.message);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
