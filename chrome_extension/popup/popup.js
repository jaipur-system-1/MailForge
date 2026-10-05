document.getElementById("open-mailforge").addEventListener("click", () => {
  const url = globalThis.MAILFORGE_CONFIG.uat
    ? globalThis.MAILFORGE_CONFIG.uatUrl
    : globalThis.MAILFORGE_CONFIG.localUrl;
  chrome.tabs.create({ url });
});

