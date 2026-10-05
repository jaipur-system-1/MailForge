(() => {
if (globalThis.__mailforgeBridgeInstalled) {
  return;
}
globalThis.__mailforgeBridgeInstalled = true;

const REQUEST_SOURCE = "mailforge-preview";
const RESPONSE_SOURCE = "mailforge-extension";
const INSERT_REQUEST = "MAILFORGE_INSERT_HTML";
const INSERT_RESULT = "MAILFORGE_INSERT_RESULT";
const MAX_HTML_LENGTH = 1_000_000;

function reply(target, origin, requestId, result) {
  target.postMessage(
    {
      source: RESPONSE_SOURCE,
      type: INSERT_RESULT,
      requestId,
      ...result,
    },
    origin === "null" ? "*" : origin
  );
}

window.addEventListener("message", event => {
  const message = event.data;
  if (
    !message ||
    message.source !== REQUEST_SOURCE ||
    message.type !== INSERT_REQUEST
  ) {
    return;
  }

  if (
    typeof message.requestId !== "string" ||
    typeof message.html !== "string" ||
    !message.html.trim() ||
    message.html.length > MAX_HTML_LENGTH
  ) {
    reply(event.source, event.origin, message.requestId, {
      ok: false,
      error: "The rendered email is invalid or too large.",
    });
    return;
  }

  chrome.runtime.sendMessage(
    {
      type: INSERT_REQUEST,
      requestId: message.requestId,
      html: message.html,
    },
    response => {
      if (chrome.runtime.lastError) {
        reply(event.source, event.origin, message.requestId, {
          ok: false,
          error: "MailForge extension is unavailable. Reload the extension and try again.",
        });
        return;
      }

      reply(event.source, event.origin, message.requestId, response || {
        ok: false,
        error: "Gmail did not return a response.",
      });
    }
  );
});
})();

