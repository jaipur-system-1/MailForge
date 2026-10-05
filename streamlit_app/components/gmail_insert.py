"""Browser bridge control for inserting a rendered email into Gmail."""

from collections.abc import Callable

import streamlit as st


COMPONENT_HTML = """
<button id="insert" type="button">Insert into Gmail</button>
<div id="status" role="status" aria-live="polite"></div>
"""


COMPONENT_CSS = """
* { box-sizing: border-box; }
:host { color: #17324d; font-family: Arial, Helvetica, sans-serif; }
button {
  width: 100%; min-height: 40px; padding: 0 14px;
  border: 1px solid #279fda; border-radius: 8px;
  background: #279fda; color: #fff; cursor: pointer;
  font-size: 14px; font-weight: 600;
}
button:hover { background: #218dc2; }
button:disabled { cursor: wait; opacity: .7; }
#status {
  min-height: 34px; margin-top: 5px; color: #61737f;
  font-size: 12px; line-height: 16px; overflow-wrap: anywhere;
}
#status.error { color: #c23b32; }
#status.success { color: #247a43; }
"""


COMPONENT_JS = """
export default function(component) {
  const { data, parentElement, setTriggerValue } = component;
  const button = parentElement.querySelector('#insert');
  const status = parentElement.querySelector('#status');
  let activeRequestId = null;
  let responseTimer = null;

  function showStatus(message, kind = '') {
    status.textContent = message;
    status.className = kind;
  }

  function resetButton() {
    button.disabled = false;
    button.textContent = 'Insert into Gmail';
  }

  function insertIntoGmail() {
    activeRequestId = crypto.randomUUID();
    button.disabled = true;
    button.textContent = 'Inserting…';
    showStatus('Looking for an open Gmail compose window…');

    window.postMessage({
      source: 'mailforge-preview',
      type: 'MAILFORGE_INSERT_HTML',
      requestId: activeRequestId,
      html: data.html,
    }, '*');

    clearTimeout(responseTimer);
    responseTimer = setTimeout(() => {
      resetButton();
      showStatus(
        'Could not connect to the extension. Reload it once and try again.',
        'error'
      );
      activeRequestId = null;
    }, 8000);
  }

  function handleExtensionResponse(event) {
    const message = event.data;
    if (
      !message ||
      message.source !== 'mailforge-extension' ||
      message.type !== 'MAILFORGE_INSERT_RESULT' ||
      message.requestId !== activeRequestId
    ) {
      return;
    }

    clearTimeout(responseTimer);
    resetButton();
    showStatus(
      message.ok ? 'Inserted into Gmail.' : message.error,
      message.ok ? 'success' : 'error'
    );
    if (message.ok) {
      setTriggerValue('inserted', Date.now());
    }
    activeRequestId = null;
  }

  button.addEventListener('click', insertIntoGmail);
  window.addEventListener('message', handleExtensionResponse);

  return () => {
    clearTimeout(responseTimer);
    button.removeEventListener('click', insertIntoGmail);
    window.removeEventListener('message', handleExtensionResponse);
  };
}
"""


gmail_insert_component = st.components.v2.component(
    "mailforge_gmail_insert",
    html=COMPONENT_HTML,
    css=COMPONENT_CSS,
    js=COMPONENT_JS,
)


def render_gmail_insert(
    html: str,
    *,
    key: str = "mailforge-gmail-insert",
    on_inserted: Callable[[], None] | None = None,
):
    """Insert HTML into Gmail and notify Streamlit after confirmed success."""
    return gmail_insert_component(
        key=key,
        data={"html": html},
        height=84,
        on_inserted_change=on_inserted,
    )
