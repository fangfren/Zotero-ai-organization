(function () {
  "use strict";

  const state = {
    categories: [],
    items: [],
    currentItem: null,
    imports: [],
    lastReport: "",
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
      <button class="app-action" id="app-import" type="button">导入文档</button>
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
      .querySelector("#app-import")
      .addEventListener("click", () => openImportModal());
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
      state.currentItem = item || null;
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
      const importButton = document.createElement("button");
      importButton.className = "action-link";
      importButton.type = "button";
      importButton.textContent = "关联资料";
      importButton.addEventListener("click", () => openImportModal(item));
      actionList?.appendChild(importButton);
      if (item?.url && /^https?:\/\//i.test(item.url)) {
        const readmeButton = document.createElement("button");
        readmeButton.className = "action-link";
        readmeButton.type = "button";
        readmeButton.textContent = "一键导入 README";
        readmeButton.addEventListener("click", () => importReadmeForItems(item));
        actionList?.appendChild(readmeButton);
      }
      renderRelatedImports(body, item);
    };
  }

  async function importReadmeForItems(item, urlOverride) {
    const url = urlOverride || item?.url || "";
    if (!url) {
      toast("这篇文献没有可用的链接。");
      return;
    }
    toast("正在抓取 README…");
    try {
      const payload = await fetchJson("/api/imports/readme", {
        method: "POST",
        body: JSON.stringify({
          url,
          item_ids: item ? [Number(item.id)] : [],
          item_keys: item && item.key ? [item.key] : [],
        }),
      });
      toast(payload.message || "README 已导入。");
      refreshRelatedImports();
    } catch (error) {
      toast(error.message);
    }
  }

  async function renderRelatedImports(body, item) {
    const section = document.createElement("section");
    section.className = "related-imports";
    section.innerHTML = '<h3>关联资料</h3><p class="report-output">正在读取…</p>';
    body.appendChild(section);
    try {
      const payload = await fetchJson(
        `/api/imports?item_id=${encodeURIComponent(item.id)}&item_key=${encodeURIComponent(item.key || "")}`
      );
      state.imports = Array.isArray(payload.imports) ? payload.imports : [];
      if (!state.imports.length) {
        section.innerHTML =
          '<h3>关联资料</h3><p class="report-output">暂无关联资料。点击“关联资料”可以导入 README、笔记或其它文本并关联到这篇文献。</p>';
        return;
      }
      section.innerHTML =
        "<h3>关联资料</h3>" +
        state.imports
          .map(
            (record) => `
              <div class="import-row">
                <div class="import-meta">
                  <strong>${escapeHtml(record.name)}</strong>
                  <span class="status-pill">${escapeHtml(record.imported_at || "")}</span>
                </div>
                <p>${escapeHtml(record.preview || "")}</p>
                <button class="app-action" type="button" data-view="${escapeHtml(record.id)}">查看全文</button>
              </div>
            `
          )
          .join("");
      section.querySelectorAll("[data-view]").forEach((button) => {
        button.addEventListener("click", () => openImportDetail(button.dataset.view));
      });
    } catch (error) {
      section.innerHTML = `<h3>关联资料</h3><p class="report-output">${escapeHtml(error.message)}</p>`;
    }
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

  function itemLinkGrid(idPrefix, selectedIds) {
    const selected = new Set((selectedIds || []).map(Number));
    const rows = state.items
      .map(
        (item) => `
          <label data-search="${escapeHtml(
            `${item.title} ${(item.authors || []).join(" ")} ${item.year || ""}`.toLowerCase()
          )}">
            <input type="checkbox" value="${item.id}" ${selected.has(Number(item.id)) ? "checked" : ""}>
            <span>${escapeHtml(item.title)}</span>
          </label>
        `
      )
      .join("");
    return `
      <div class="app-field full">
        <label>关联文献</label>
        <div class="link-tools">
          <input type="search" id="${idPrefix}-filter" placeholder="按标题或作者筛选">
          <button class="app-action" type="button" data-link-all>全选可见</button>
          <button class="app-action" type="button" data-link-none>清空</button>
        </div>
        <div class="checkbox-grid scroll" id="${idPrefix}-links">
          ${rows || '<p class="report-output">文献库为空，导入的资料会先保存为未关联资料。</p>'}
        </div>
      </div>
    `;
  }

  function installLinkTools(root, idPrefix) {
    if (!root) return;
    const filter = root.querySelector(`#${idPrefix}-filter`);
    const grid = root.querySelector(`#${idPrefix}-links`);
    if (grid) {
      filter?.addEventListener("input", () => {
        const keyword = filter.value.trim().toLowerCase();
        grid.querySelectorAll("label").forEach((label) => {
          const hit = !keyword || (label.dataset.search || "").includes(keyword);
          label.style.display = hit ? "" : "none";
        });
      });
      root.querySelector("[data-link-all]")?.addEventListener("click", () => {
        grid.querySelectorAll("label").forEach((label) => {
          if (label.style.display !== "none") {
            const input = label.querySelector("input");
            if (input) input.checked = true;
          }
        });
      });
      root.querySelector("[data-link-none]")?.addEventListener("click", () => {
        grid.querySelectorAll("input").forEach((input) => {
          input.checked = false;
        });
      });
    }
  }

  function selectedLinkIds(root, idPrefix) {
    const grid = root?.querySelector(`#${idPrefix}-links`);
    if (!grid) return [];
    return [...grid.querySelectorAll('input[type="checkbox"]:checked')].map((input) =>
      Number(input.value)
    );
  }

  function keysForItemIds(ids) {
    return (ids || [])
      .map((id) => state.items.find((item) => Number(item.id) === Number(id))?.key)
      .filter(Boolean);
  }

  function existingImportsHtml(records) {
    if (!records.length) return '<p class="report-output">还没有导入任何资料。</p>';
    return records
      .map(
        (record) => `
          <div class="import-row" data-import-id="${escapeHtml(record.id)}">
            <div class="import-meta">
              <strong>${escapeHtml(record.name)}</strong>
              <span class="status-pill">${(record.item_ids || []).length} 篇关联</span>
              <span class="status-pill">${Math.max(1, Math.round((record.size || 0) / 1024))} KB</span>
              <span class="status-pill">${escapeHtml(record.imported_at || "")}</span>
            </div>
            <p>${escapeHtml(record.preview || "")}</p>
            <div class="import-actions">
              <button class="app-action" type="button" data-view>查看 / 关联</button>
              <button class="app-action danger" type="button" data-delete>删除</button>
            </div>
          </div>
        `
      )
      .join("");
  }

  function bindImportRows(root) {
    if (!root) return;
    root.querySelectorAll(".import-row[data-import-id]").forEach((row) => {
      row.querySelector("[data-view]")?.addEventListener("click", () =>
        openImportDetail(row.dataset.importId)
      );
      row.querySelector("[data-delete]")?.addEventListener("click", async () => {
        if (!window.confirm("删除这份导入资料？")) return;
        try {
          await fetchJson(`/api/imports/${encodeURIComponent(row.dataset.importId)}`, {
            method: "DELETE",
          });
          row.remove();
          toast("资料已删除。");
          refreshRelatedImports();
        } catch (error) {
          toast(error.message);
        }
      });
    });
  }

  async function refreshRelatedImports() {
    const item = state.currentItem;
    const body = document.querySelector("#detail-body");
    if (!item || !body) return;
    body.querySelectorAll(".related-imports").forEach((section) => section.remove());
    renderRelatedImports(body, item);
  }

  async function openImportModal(presetItem) {
    let payload;
    try {
      payload = await fetchJson("/api/imports");
    } catch (error) {
      toast(error.message);
      return;
    }
    const existing = Array.isArray(payload.imports) ? payload.imports : [];
    const presetIds = presetItem ? [Number(presetItem.id)] : [];
    const body = `
      <div class="status-row">
        <span class="status-pill">已导入 ${existing.length} 份资料</span>
        <span class="status-pill">支持 .md / .markdown / .txt 等文本文件</span>
      </div>
      <div class="app-grid">
        <div class="app-field full">
          <label>一键导入 README（GitHub 仓库、raw 或文本链接）</label>
          <div class="import-url-row">
            <input type="url" id="import-readme-url" placeholder="https://github.com/用户名/仓库" value="${escapeHtml(
              presetItem?.url && /^https?:\/\//i.test(presetItem.url) ? presetItem.url : ""
            )}">
            <button class="app-action" id="import-readme" type="button">抓取 README</button>
          </div>
          <p class="app-hint">仓库地址会自动尝试 README.md / README.rst / README.txt，抓取后会按下面的勾选关联文献。</p>
        </div>
        <div class="app-field full">
          <label>导入文件（可多选，也可以直接拖进来）</label>
          <div class="dropzone" id="import-dropzone">
            <input type="file" id="import-files" multiple accept=".md,.markdown,.txt,.rst,.json,.yml,.yaml,.csv">
            <p>把 README、笔记或整理文档拖到这里，或点击选择文件</p>
          </div>
        </div>
        <div class="app-field full">
          <label>或直接粘贴文本</label>
          <input type="text" id="import-name" placeholder="资料名称，例如 README-项目说明">
          <textarea id="import-text" placeholder="粘贴 Markdown 或纯文本内容"></textarea>
        </div>
        ${itemLinkGrid("import", presetIds)}
        <div class="full">
          <h3 class="category-section-title">已导入资料</h3>
          <div id="import-existing">${existingImportsHtml(existing)}</div>
        </div>
      </div>
    `;
    const footer = `
      <button class="app-action primary" id="import-save" type="button">导入并关联</button>
    `;
    showModal(modalShell("导入 README / 资料", body, footer));
    const modal = document.querySelector("#app-modal");
    installLinkTools(modal, "import");
    bindImportRows(modal.querySelector("#import-existing"));

    let pendingFiles = [];
    const dropzone = modal.querySelector("#import-dropzone");
    const fileInput = modal.querySelector("#import-files");
    const dropText = dropzone.querySelector("p");
    const showFiles = () => {
      if (!pendingFiles.length) return;
      dropText.textContent = `已选择 ${pendingFiles.length} 个文件：${pendingFiles
        .map((file) => file.name)
        .join("、")}`;
    };
    dropzone.addEventListener("click", (event) => {
      if (event.target !== fileInput) fileInput.click();
    });
    ["dragenter", "dragover"].forEach((name) =>
      dropzone.addEventListener(name, (event) => {
        event.preventDefault();
        dropzone.classList.add("active");
      })
    );
    ["dragleave", "drop"].forEach((name) =>
      dropzone.addEventListener(name, (event) => {
        event.preventDefault();
        dropzone.classList.remove("active");
      })
    );
    dropzone.addEventListener("drop", (event) => {
      const dropped = [...(event.dataTransfer?.files || [])];
      if (dropped.length) {
        pendingFiles = dropped;
        showFiles();
      }
    });
    fileInput.addEventListener("change", () => {
      pendingFiles = [...fileInput.files];
      showFiles();
    });

    modal.querySelector("#import-readme").addEventListener("click", async () => {
      const url = modal.querySelector("#import-readme-url").value.trim();
      if (!url) {
        toast("请先填写仓库地址或 README 链接。");
        return;
      }
      const ids = selectedLinkIds(modal, "import");
      try {
        const result = await fetchJson("/api/imports/readme", {
          method: "POST",
          body: JSON.stringify({
            url,
            item_ids: ids,
            item_keys: keysForItemIds(ids),
          }),
        });
        toast(result.message || "README 已导入。");
        refreshRelatedImports();
        openImportModal(presetItem);
      } catch (error) {
        toast(error.message);
      }
    });

    modal.querySelector("#import-save").addEventListener("click", async () => {
      const customName = modal.querySelector("#import-name").value.trim();
      const entries = [];
      for (const file of pendingFiles) {
        entries.push({
          name: pendingFiles.length === 1 && customName ? customName : file.name,
          content: await file.text(),
        });
      }
      const pasted = modal.querySelector("#import-text").value;
      if (pasted.trim()) {
        entries.push({ name: customName || "粘贴资料", content: pasted });
      }
      if (!entries.length) {
        toast("请选择文件或粘贴文本。");
        return;
      }
      const ids = selectedLinkIds(modal, "import");
      try {
        const result = await fetchJson("/api/imports", {
          method: "POST",
          body: JSON.stringify({
            entries,
            item_ids: ids,
            item_keys: keysForItemIds(ids),
            source: "ui",
          }),
        });
        toast(result.message || "导入完成。");
        refreshRelatedImports();
        openImportModal(presetItem);
      } catch (error) {
        toast(error.message);
      }
    });
  }

  async function openImportDetail(importId) {
    let payload;
    try {
      payload = await fetchJson(`/api/imports/${encodeURIComponent(importId)}`);
    } catch (error) {
      toast(error.message);
      return;
    }
    const record = payload.import || {};
    const body = `
      <div class="status-row">
        <span class="status-pill">${escapeHtml(record.imported_at || "")}</span>
        <span class="status-pill">${Math.max(1, Math.round((record.size || 0) / 1024))} KB</span>
      </div>
      ${itemLinkGrid("importdetail", record.item_ids || [])}
      <p class="report-output tall">${escapeHtml(record.content || "")}</p>
    `;
    const footer = `
      <button class="app-action primary" id="importdetail-save" type="button">保存关联</button>
    `;
    showModal(modalShell(record.name || "导入资料", body, footer));
    const modal = document.querySelector("#app-modal");
    installLinkTools(modal, "importdetail");
    modal.querySelector("#importdetail-save").addEventListener("click", async () => {
      const ids = selectedLinkIds(modal, "importdetail");
      try {
        await fetchJson(`/api/imports/${encodeURIComponent(importId)}`, {
          method: "PUT",
          body: JSON.stringify({ item_ids: ids, item_keys: keysForItemIds(ids) }),
        });
        toast("关联文献已更新。");
        refreshRelatedImports();
        openImportModal();
      } catch (error) {
        toast(error.message);
      }
    });
  }

  function aiStatusPills(config) {
    if (!config) return '<span class="status-pill bad">无法读取 AI 设置</span>';
    const pills = [];
    if (config.provider === "codex") {
      pills.push(
        `<span class="status-pill ${config.codex_available ? "ok" : "bad"}">${
          config.codex_available ? "已找到 Codex" : "未找到 Codex"
        }</span>`
      );
      pills.push(
        `<span class="status-pill ${
          config.codex_logged_in === false ? "bad" : "ok"
        }">${
          config.codex_logged_in === false
            ? "Codex 未登录"
            : config.codex_logged_in
              ? "订阅登录正常"
              : "登录状态未知"
        }</span>`
      );
      pills.push('<span class="status-pill">无需 API 密钥</span>');
    } else {
      pills.push(
        `<span class="status-pill ${config.configured ? "ok" : "bad"}">${
          config.configured ? "API 已配置" : "API 未配置"
        }</span>`
      );
    }
    pills.push(
      `<span class="status-pill">关联资料 ${Number(config.import_count || 0)} 份</span>`
    );
    return pills.join("");
  }

  function codexStatusHtml(config) {
    if (!config) return "";
    if (config.provider !== "codex") {
      return '<p class="app-hint">当前使用 OpenAI 兼容 API 生成报告。想改用订阅登录，请在“AI 设置”里切换到 Codex。</p>';
    }
    const lines = [];
    if (config.codex_path) {
      lines.push(
        `<p class="app-hint">Codex：<code>${escapeHtml(config.codex_path)}</code>${
          config.codex_version ? `（${escapeHtml(config.codex_version)}）` : ""
        }</p>`
      );
    } else {
      lines.push(
        '<p class="app-hint">没有找到 Codex CLI。请安装 Codex 并在“AI 设置 → Codex 命令”里填写完整路径。</p>'
      );
      const candidates = Array.isArray(config.codex_candidates)
        ? config.codex_candidates.slice(0, 3)
        : [];
      if (candidates.length) {
        lines.push(
          `<p class="app-hint">已探测到的候选：${candidates
            .map((value) => `<code>${escapeHtml(value)}</code>`)
            .join("、")}</p>`
        );
      }
    }
    if (config.codex_logged_in === false) {
      lines.push(
        '<p class="app-hint">Codex 尚未登录：在终端执行 <code>codex login</code> 完成订阅登录。</p>'
      );
    }
    if (config.opencode_available && !config.codex_available) {
      lines.push(
        '<p class="app-hint">检测到 opencode：本工作台固定调用 codex 命令，请在上面“Codex 命令”里填写 codex 可执行文件的完整路径。</p>'
      );
    }
    if (config.codex_error) {
      lines.push(
        `<p class="app-hint">探测信息：${escapeHtml(config.codex_error)}</p>`
      );
    }
    return lines.join("");
  }

  async function openReportModal() {
    let aiConfig = null;
    try {
      aiConfig = await fetchJson("/api/ai/config?probe=1");
    } catch (error) {
      toast(error.message);
    }
    const templates =
      Array.isArray(aiConfig?.templates) && aiConfig.templates.length
        ? aiConfig.templates
        : [{ id: "research", label: "研究问题—方法—结论", sections: [] }];
    const defaultTemplate = templates.some(
      (template) => template.id === aiConfig?.report_template
    )
      ? aiConfig.report_template
      : templates[0].id;
    const options = state.items
      .map(
        (item) =>
          `<option value="${item.id}">${escapeHtml(item.title)}</option>`
      )
      .join("");
    const body = `
      <div class="status-row">
        ${aiStatusPills(aiConfig)}
      </div>
      <div class="codex-status" id="report-codex-status">${codexStatusHtml(aiConfig)}</div>
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
          <label>报告模板</label>
          <select id="report-template">
            ${templates
              .map(
                (template) =>
                  `<option value="${escapeHtml(template.id)}" ${
                    template.id === defaultTemplate ? "selected" : ""
                  }>${escapeHtml(template.label)}</option>`
              )
              .join("")}
          </select>
          <p class="app-hint" id="report-template-hint"></p>
        </div>
        <div class="app-field full">
          <label>补充要求（可留空）</label>
          <textarea id="report-instruction" placeholder="例如：按 DFB 可靠性研究方向整理，区分原理、测量方法和挑战。"></textarea>
        </div>
        <div class="full" id="report-result"></div>
      </div>
    `;
    const footer = `
      <button class="app-action" id="report-codex-test" type="button">测试 Codex</button>
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

    const templateSelect = document.querySelector("#report-template");
    const templateHint = document.querySelector("#report-template-hint");
    const showTemplateHint = () => {
      const template = templates.find((entry) => entry.id === templateSelect.value);
      const sections = Array.isArray(template?.sections) ? template.sections : [];
      templateHint.textContent = sections.length
        ? `报告章节：${sections.join(" / ")}`
        : "不使用固定章节，完全按补充要求组织报告。";
    };
    templateSelect.addEventListener("change", showTemplateHint);
    showTemplateHint();

    const selectedIds = () => {
      if (scope.value === "item") {
        return [Number(document.querySelector("#report-item").value)];
      }
      return null;
    };
    const instruction = () =>
      document.querySelector("#report-instruction").value.trim();

    document
      .querySelector("#report-codex-test")
      .addEventListener("click", async () => {
        const hint = document.querySelector("#report-codex-status");
        hint.innerHTML = '<p class="report-output">正在调用 Codex 自检，可能需要十几秒…</p>';
        try {
          const payload = await fetchJson("/api/ai/test", {
            method: "POST",
            body: JSON.stringify({}),
          });
          hint.innerHTML = `
            <p class="${payload.ok ? "status-pill ok" : "status-pill bad"}">${
              payload.ok ? "Codex 连接正常" : "Codex 调用失败"
            }</p>
            <p class="report-output">${escapeHtml(payload.message || "")}</p>
            ${payload.preview ? `<pre class="report-output">${escapeHtml(payload.preview)}</pre>` : ""}
          `;
        } catch (error) {
          hint.innerHTML = `<p class="status-pill bad">调用失败</p><p class="report-output">${escapeHtml(error.message)}</p>`;
        }
      });

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
              template: templateSelect.value,
            }),
          });
          state.lastReport = payload.report || "";
          document.querySelector("#report-result").innerHTML = `
            <p class="status-pill ${payload.ai_used ? "ok" : "bad"}">${escapeHtml(payload.message || "")}</p>
            <pre class="report-output tall">${escapeHtml(payload.report || "")}</pre>
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
              template: templateSelect.value,
              report: state.lastReport || "",
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
      config = await fetchJson("/api/ai/config?probe=1");
    } catch (error) {
      toast(error.message);
      return;
    }
    const body = `
      <div class="status-row">
        ${aiStatusPills(config)}
      </div>
      <div class="codex-status">${codexStatusHtml(config)}</div>
      <div class="app-grid">
        <div class="app-field full">
          <label>报告生成方式</label>
          <select id="ai-provider">
            <option value="codex" ${config.provider === "codex" ? "selected" : ""}>Codex 订阅登录（无需 API 密钥）</option>
            <option value="api" ${config.provider === "api" ? "selected" : ""}>OpenAI 兼容 API</option>
          </select>
        </div>
        <div class="app-field full" id="codex-fields" ${config.provider === "api" ? 'style="display:none"' : ""}>
          <div class="app-grid">
            <div class="app-field full">
              <label>Codex 命令路径（留空则自动探测）</label>
              <input type="text" id="ai-codex-command" value="${escapeHtml(config.codex_command)}" placeholder="例如 C:\\Users\\you\\AppData\\Local\\OpenAI\\Codex\\bin\\codex.exe">
            </div>
            <div class="app-field">
              <label>模型（留空使用默认）</label>
              <input type="text" id="ai-codex-model" value="${escapeHtml(config.codex_model)}" placeholder="例如 gpt-5-codex">
            </div>
            <div class="app-field">
              <label>超时（秒）</label>
              <input type="number" id="ai-codex-timeout" min="60" max="3600" step="30" value="${Number(config.codex_timeout) || 600}">
            </div>
            <div class="app-field full">
              <label>额外参数（可选）</label>
              <input type="text" id="ai-codex-extra-args" value="${escapeHtml(config.codex_extra_args)}" placeholder="例如 --skip-git-repo-check">
            </div>
          </div>
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
        <div class="full" id="ai-test-result"></div>
      </div>
    `;
    const footer = `
      <button class="app-action" id="ai-test" type="button">测试 Codex</button>
      <button class="app-action primary" id="ai-save" type="button">保存设置</button>
    `;
    showModal(modalShell("AI 设置", body, footer));
    const providerSelect = document.querySelector("#ai-provider");
    const apiFields = document.querySelector("#api-fields");
    const codexFields = document.querySelector("#codex-fields");
    providerSelect.addEventListener("change", () => {
      apiFields.style.display = providerSelect.value === "api" ? "" : "none";
      codexFields.style.display = providerSelect.value === "codex" ? "" : "none";
    });
    document.querySelector("#ai-test").addEventListener("click", async () => {
      const result = document.querySelector("#ai-test-result");
      result.innerHTML = '<p class="report-output">正在调用 Codex 自检，可能需要十几秒…</p>';
      try {
        const payload = await fetchJson("/api/ai/test", {
          method: "POST",
          body: JSON.stringify({
            model: document.querySelector("#ai-codex-model").value.trim(),
          }),
        });
        result.innerHTML = `
          <p class="status-pill ${payload.ok ? "ok" : "bad"}">${
            payload.ok ? "Codex 连接正常" : "Codex 调用失败"
          }</p>
          <p class="report-output">${escapeHtml(payload.message || "")}</p>
          <p class="app-hint">命令：<code>${escapeHtml(payload.path || "未找到")}</code>${
            payload.version ? `（${escapeHtml(payload.version)}）` : ""
          }${payload.login ? `　登录：${escapeHtml(payload.login)}` : ""}</p>
          ${payload.preview ? `<pre class="report-output">${escapeHtml(payload.preview)}</pre>` : ""}
        `;
      } catch (error) {
        result.innerHTML = `<p class="status-pill bad">调用失败</p><p class="report-output">${escapeHtml(error.message)}</p>`;
      }
    });
    document.querySelector("#ai-save").addEventListener("click", async () => {
      const payload = { provider: providerSelect.value };
      if (providerSelect.value === "codex") {
        payload.codex_command = document.querySelector("#ai-codex-command").value.trim();
        payload.codex_model = document.querySelector("#ai-codex-model").value.trim();
        payload.codex_extra_args = document.querySelector("#ai-codex-extra-args").value.trim();
        payload.codex_timeout =
          Number(document.querySelector("#ai-codex-timeout").value) || 600;
      }
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
