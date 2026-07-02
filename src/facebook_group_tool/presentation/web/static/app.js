document.documentElement.dataset.ready = "true";

/**
 * @param {unknown} value
 * @returns {value is { status: string, synced_count?: number, message?: string }}
 */
function isSyncResponse(value) {
  return typeof value === "object" && value !== null && "status" in value;
}

/**
 * @param {string} message
 * @returns {void}
 */
function updateSyncStatus(message) {
  const statusElement = document.querySelector("#sync-status");
  if (statusElement instanceof HTMLElement) {
    statusElement.textContent = message;
  }
}

/**
 * @param {string} endpoint
 * @returns {Promise<void>}
 */
async function postSyncAction(endpoint) {
  try {
    updateSyncStatus("Status: working...");
    const response = await fetch(endpoint, { method: "POST" });
    const payload = await response.json();
    if (!response.ok || !isSyncResponse(payload)) {
      updateSyncStatus("Status: request failed");
      return;
    }
    const count = typeof payload.synced_count === "number" ? ` (${payload.synced_count} groups)` : "";
    updateSyncStatus(`Status: ${payload.status}${count}`);
    if (endpoint.endsWith("collect-visible")) {
      window.location.reload();
    }
  } catch (_error) {
    updateSyncStatus("Status: network error");
  }
}

const actionMap = {
  "start-sync": "/api/automation/group-sync/start",
  "collect-visible": "/api/automation/group-sync/collect-visible",
  "stop-sync": "/api/automation/group-sync/stop",
};

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const action = target.dataset.action;
  if (!action || !(action in actionMap)) {
    return;
  }
  void postSyncAction(actionMap[action]);
});
