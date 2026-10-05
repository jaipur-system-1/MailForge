importScripts("config.js");

const INSERT_REQUEST = "MAILFORGE_INSERT_HTML";
const ACTIVE_MAILFORGE_URL = globalThis.MAILFORGE_CONFIG.uat
  ? globalThis.MAILFORGE_CONFIG.uatUrl
  : globalThis.MAILFORGE_CONFIG.localUrl;
const TRUSTED_MAILFORGE_URLS = [ACTIVE_MAILFORGE_URL];
const EXISTING_TAB_SCRIPTS = [
  {
    urls: [`${ACTIVE_MAILFORGE_URL}*`],
    file: "mailforge-bridge.js",
  },
  {
    urls: ["https://mail.google.com/*"],
    file: "gmail-content-script.js",
  },
];

async function injectIntoExistingTabs() {
  for (const entry of EXISTING_TAB_SCRIPTS) {
    const tabs = await chrome.tabs.query({ url: entry.urls });
    await Promise.allSettled(
      tabs
        .filter(tab => tab.id)
        .map(tab => chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: [entry.file],
        }))
    );
  }
}

chrome.runtime.onInstalled.addListener(() => {
  injectIntoExistingTabs().catch(() => {
    // Normal manifest injection remains available after a page reload.
  });
});

function isTrustedSender(sender) {
  return TRUSTED_MAILFORGE_URLS.some(prefix => sender.url?.startsWith(prefix));
}

async function findGmailTab() {
  const tabs = await chrome.tabs.query({ url: "https://mail.google.com/*" });
  return tabs.find(tab => tab.active) || tabs[0] || null;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== INSERT_REQUEST) {
    return false;
  }

  if (!isTrustedSender(sender)) {
    sendResponse({ ok: false, error: "The insertion request was not trusted." });
    return false;
  }

  (async () => {
    const gmailTab = await findGmailTab();
    if (!gmailTab?.id) {
      return {
        ok: false,
        error: "Open Gmail and start a compose window, then try again.",
      };
    }

    try {
      return await chrome.tabs.sendMessage(gmailTab.id, {
        type: INSERT_REQUEST,
        requestId: message.requestId,
        html: message.html,
      });
    } catch (_error) {
      return {
        ok: false,
        error: "Reload Gmail once so the MailForge extension can connect.",
      };
    }
  })()
    .then(sendResponse)
    .catch(() => {
      sendResponse({
        ok: false,
        error: "MailForge could not communicate with Gmail.",
      });
    });

  return true;
});

