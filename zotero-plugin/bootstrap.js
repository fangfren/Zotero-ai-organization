/* Research Workbench -- Zotero plugin bootstrap.
 * Loaded by Zotero as a bootstrap add-on; see manifest.json.
 */

var chromeHandle;
var workbenchScope;

function install() {}

async function startup({ id, version, resourceURI, rootURI }) {
  if (!rootURI) {
    rootURI = resourceURI.spec;
  }
  const aomStartup = Components.classes["@mozilla.org/addons/addon-manager-startup;1"]
    .getService(Components.interfaces.amIAddonManagerStartup);
  const manifestURI = Services.io.newURI(rootURI + "manifest.json");
  chromeHandle = aomStartup.registerChrome(manifestURI, [
    ["content", "researchworkbench", rootURI + "content/"],
  ]);

  const scope = {
    rootURI,
    pluginID: id,
    pluginVersion: version,
  };
  scope._globalThis = scope;
  workbenchScope = scope;

  Services.scriptloader.loadSubScriptWithOptions(rootURI + "content/workbench.js", {
    target: scope,
    ignoreCache: true,
  });

  if (scope.ResearchWorkbench) {
    await scope.ResearchWorkbench.startup({ id, version, rootURI });
  } else {
    Zotero.logError(new Error("Research Workbench: content/workbench.js did not load"));
  }
}

async function shutdown({ id }, reason) {
  if (reason === APP_SHUTDOWN) {
    return;
  }
  try {
    if (workbenchScope && workbenchScope.ResearchWorkbench) {
      await workbenchScope.ResearchWorkbench.shutdown({ id });
    }
  } catch (error) {
    Zotero.logError(error);
  }
  if (chromeHandle) {
    chromeHandle.destruct();
    chromeHandle = null;
  }
  workbenchScope = null;
}

async function onMainWindowLoad({ window }) {
  if (workbenchScope && workbenchScope.ResearchWorkbench) {
    await workbenchScope.ResearchWorkbench.onMainWindowLoad(window);
  }
}

async function onMainWindowUnload({ window }) {
  if (workbenchScope && workbenchScope.ResearchWorkbench) {
    await workbenchScope.ResearchWorkbench.onMainWindowUnload(window);
  }
}

function uninstall() {}
