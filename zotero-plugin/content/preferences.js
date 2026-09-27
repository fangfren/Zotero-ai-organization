/*
 * Preferences pane for Research Workbench.
 *
 * Zotero loads pane scripts before inserting the XHTML fragment, so initialise
 * asynchronously and wait until the pane markup exists.
 */

/* global Zotero, document, setTimeout */

(function () {
	"use strict";

	const DEFAULTS = Object.freeze({
		codexPath: "",
		model: "",
		extraArgs: "",
		timeout: 600,
		template: "research",
		reportLanguage: "auto",
		includePdfText: true,
		includeAnnotations: true,
		includeNotes: true,
		includeAttachments: true,
		includeImportedMaterial: true,
		maxContextChars: 60000,
		importContentLimit: 20000,
		openNoteAfterGeneration: true,
		addReportTag: true,
		lastInstruction: "",
	});

	let initAttempts = 0;
	let initialized = false;

	function api() {
		return Zotero.ResearchWorkbench;
	}

	function pref(name, fallback) {
		const workbench = api();
		if (workbench && typeof workbench.getPref === "function") {
			return workbench.getPref(name, fallback);
		}
		return fallback;
	}

	function setPref(name, value) {
		const workbench = api();
		if (workbench && typeof workbench.setPref === "function") {
			workbench.setPref(name, value);
		}
	}

	function localize(key, ...args) {
		const workbench = api();
		if (workbench && typeof workbench.localize === "function") {
			return workbench.localize(key, ...args);
		}
		return key;
	}

	function byID(id) {
		return document.getElementById(id);
	}

	function setStatus(message, type) {
		const status = byID("rw-codex-status");
		if (!status) {
			return;
		}
		status.textContent = String(message || "");
		status.classList.toggle("is-error", type === "error");
		status.classList.toggle("is-ok", type === "ok");
	}

	function markSaved() {
		setStatus(localize("settingsSaved"), "ok");
	}

	function bindText(id, name, transform) {
		const control = byID(id);
		if (!control) {
			return;
		}
		control.value = String(pref(name, DEFAULTS[name]) || "");
		control.addEventListener("input", () => {
			let value = control.value;
			if (transform) {
				value = transform(value);
			}
			if (value !== null) {
				setPref(name, value);
				markSaved();
			}
		});
	}

	function bindNumber(id, name, min, max) {
		bindText(id, name, (raw) => {
			if (String(raw).trim() === "") {
				return null;
			}
			let value = Number(raw);
			if (!Number.isFinite(value)) {
				return null;
			}
			value = Math.round(value);
			value = Math.max(min, Math.min(max, value));
			return value;
		});
	}

	function bindCheckbox(id, name) {
		const control = byID(id);
		if (!control) {
			return;
		}
		control.checked = !!pref(name, DEFAULTS[name]);
		control.addEventListener("change", () => {
			setPref(name, !!control.checked);
			markSaved();
		});
	}

	function bindSelect(id, name) {
		const control = byID(id);
		if (!control) {
			return;
		}
		control.value = String(pref(name, DEFAULTS[name]) || DEFAULTS[name]);
		control.addEventListener("change", () => {
			setPref(name, String(control.value || DEFAULTS[name]));
			markSaved();
		});
	}

	async function refreshCodexStatus() {
		const workbench = api();
		if (!workbench || typeof workbench.codexStatus !== "function") {
			setStatus(localize("prefsUnavailable"), "error");
			return;
		}
		try {
			const status = await workbench.codexStatus();
			if (status.available) {
				const detail = [status.path, status.version].filter(Boolean).join("\n");
				setStatus(detail, "ok");
			}
			else {
				setStatus(status.message || localize("cmdMissing"), "error");
			}
		}
		catch (error) {
			setStatus(String(error && error.message ? error.message : error), "error");
		}
	}

	async function testCodex() {
		const button = byID("rw-test-codex");
		const workbench = api();
		if (!workbench || typeof workbench.runCodexSelfTest !== "function") {
			setStatus(localize("prefsUnavailable"), "error");
			return;
		}
		if (button) {
			button.disabled = true;
		}
		setStatus(localize("testing"), "");
		try {
			const result = await workbench.runCodexSelfTest();
			setStatus(result.message || (result.ok ? localize("testOk") : localize("testFail")), result.ok ? "ok" : "error");
		}
		catch (error) {
			setStatus(String(error && error.message ? error.message : error), "error");
		}
		finally {
			if (button) {
				button.disabled = false;
			}
		}
	}

	function resetPrefs() {
		Object.entries(DEFAULTS).forEach(([name, value]) => {
			setPref(name, value);
		});
		loadControls();
		setStatus(localize("settingsReset"), "ok");
		void refreshCodexStatus();
	}

	function loadControls() {
		bindText("rw-codex-path", "codexPath");
		bindText("rw-model", "model");
		bindText("rw-extra-args", "extraArgs");
		bindNumber("rw-timeout", "timeout", 60, 3600);
		bindSelect("rw-template", "template");
		bindSelect("rw-report-language", "reportLanguage");
		bindText("rw-report-instruction", "lastInstruction");
		bindCheckbox("rw-include-pdf", "includePdfText");
		bindCheckbox("rw-include-annotations", "includeAnnotations");
		bindCheckbox("rw-include-notes", "includeNotes");
		bindCheckbox("rw-include-attachments", "includeAttachments");
		bindCheckbox("rw-include-imported", "includeImportedMaterial");
		bindNumber("rw-max-context-chars", "maxContextChars", 4000, 500000);
		bindNumber("rw-import-content-limit", "importContentLimit", 1000, 100000);
		bindCheckbox("rw-open-note", "openNoteAfterGeneration");
		bindCheckbox("rw-add-report-tag", "addReportTag");
	}

	function init() {
		if (initialized) {
			return;
		}
		if (!byID("rw-prefs")) {
			initAttempts++;
			if (initAttempts < 120) {
				setTimeout(init, 25);
			}
			return;
		}
		initialized = true;
		loadControls();

		const testButton = byID("rw-test-codex");
		if (testButton) {
			testButton.addEventListener("click", testCodex);
		}
		const resetButton = byID("rw-reset-prefs");
		if (resetButton) {
			resetButton.addEventListener("click", resetPrefs);
		}
		void refreshCodexStatus();
	}

	setTimeout(init, 0);
})();
