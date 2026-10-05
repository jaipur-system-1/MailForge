(() => {
if (globalThis.__mailforgeGmailScriptInstalled) {
  return;
}
globalThis.__mailforgeGmailScriptInstalled = true;

const INSERT_REQUEST = "MAILFORGE_INSERT_HTML";

function isVisible(element) {
  const style = window.getComputedStyle(element);
  return style.display !== "none" && style.visibility !== "hidden";
}

function findComposeBody() {
  const selectors = [
    'div[contenteditable="true"][role="textbox"][aria-label*="Message Body"]',
    'div[contenteditable="true"][role="textbox"][aria-label*="message body"]',
    'div.Am.Al.editable[contenteditable="true"]',
  ];
  const candidates = [...new Set(
    selectors.flatMap(selector => [...document.querySelectorAll(selector)])
  )].filter(isVisible);

  return candidates.at(-1) || null;
}

function insertionMarkup(rawHtml) {
  const parsed = new DOMParser().parseFromString(rawHtml, "text/html");

  parsed.querySelectorAll("script, iframe, object, embed, form").forEach(element => {
    element.remove();
  });
  parsed.querySelectorAll("*").forEach(element => {
    [...element.attributes].forEach(attribute => {
      if (attribute.name.toLowerCase().startsWith("on")) {
        element.removeAttribute(attribute.name);
      }
    });
  });

  const styles = [...parsed.head.querySelectorAll("style")]
    .map(style => style.outerHTML)
    .join("");
  return `${styles}${parsed.body.innerHTML}`;
}

function insertIntoCompose(compose, rawHtml) {
  const markup = insertionMarkup(rawHtml);
  if (!markup.trim()) {
    throw new Error("The rendered email is empty.");
  }

  compose.focus();
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(compose);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);

  const inserted = document.execCommand("insertHTML", false, markup);
  if (!inserted) {
    range.insertNode(range.createContextualFragment(markup));
  }

  compose.dispatchEvent(new InputEvent("input", {
    bubbles: true,
    inputType: "insertFromPaste",
  }));
  compose.dispatchEvent(new Event("change", { bubbles: true }));
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== INSERT_REQUEST) {
    return false;
  }

  const compose = findComposeBody();
  if (!compose) {
    sendResponse({
      ok: false,
      error: "Open a Gmail compose window, then try again.",
    });
    return false;
  }

  try {
    insertIntoCompose(compose, message.html);
    sendResponse({ ok: true });
  } catch (_error) {
    sendResponse({
      ok: false,
      error: "Gmail could not insert the rendered email.",
    });
  }

  return false;
});
})();

