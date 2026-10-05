# MailForge

MailForge is an internal email-template tool built with Streamlit and Django.
Employees select an authorized, locked HTML template, enter the recipient
company name, and review the rendered email. A lightweight Chrome extension
inserts the email into an open Gmail compose window, where final text changes
can be made before sending.

## Main applications

- `streamlit_app/`: employee template selection, recipient setup, and preview
- `django_backend/`: authentication, authorization, and template rendering API
- `email_templates/`: locked HTML templates and editable-field definitions
- `chrome_extension/`: bridge between MailForge and Gmail

Templates are stored as files. SQLite is reserved for Django users, groups,
permissions, and sessions.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python django_backend\manage.py migrate
python django_backend\manage.py createsuperuser
python django_backend\manage.py runserver
```

In a second PowerShell window:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app\app.py
```

Open `http://localhost:8501` and sign in with the Django user. Logging out
revokes the active API token and clears the Streamlit session.

## Chrome extension and Gmail insertion

1. Open `chrome://extensions`, enable **Developer mode**, and choose
   **Load unpacked**.
2. Select the repository's `chrome_extension` directory.
3. In MailForge, choose a template and enter the recipient company name.
4. Review the generated read-only preview in Desktop or Mobile view.
5. Open or reload Gmail in the same Chrome profile and start a compose window.
6. Select **Insert into Gmail** in MailForge and wait for confirmation.
7. Switch to Gmail, make any final text changes, and review the complete message
   before sending.
8. Return to MailForge and select **Prepare another email** for the next recipient.

MailForge clears the prepared email after Gmail confirms a successful insertion.
Logging out also clears unfinished recipient details.

## Email history

Each user has a private **Email History** page. After Gmail confirms an
insertion, MailForge records the template name, recipient company, and
insertion date and time. History does not save an email snapshot because users
can alter the content in Gmail after insertion. History confirms insertion into
Gmail; it does not confirm that the Gmail message was sent.

After changing extension code locally, reload the extension on
`chrome://extensions` and reload the Gmail tab before testing again.

## Super Admin template management

Users with Django's `is_superuser` flag see **Create/Edit Templates** and
**Create User** options in the sidebar after signing in. These pages manage
template HTML, editable fields, access groups, active status, and employee
accounts. Their API endpoints reject all non-superusers, including ordinary
staff accounts.

The user-management page lists existing accounts and allows confirmed deletion
of non-superusers. The active Super Admin account is protected. Confirmed
template deletion removes the template from the registry and moves its source
directory to `email_templates/.trash/` for manual recovery.

After upgrading an existing running session, log out and sign in again so the
frontend receives the Super Admin flag.

## Tests

Run the backend test suite from the Django project directory:

```powershell
cd django_backend
python manage.py test
```

## UAT configuration

MailForge has an explicit UAT switch. Copy `.env.example` to `.env`, replace
the placeholder secret, and keep the private `.env` file out of source control.

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Put the generated value in `DJANGO_SECRET_KEY`. The important switches are:

```dotenv
MAILFORGE_UAT=true
DJANGO_DEBUG=false
```

Use `MAILFORGE_UAT=false` for local development. Boolean settings accept
`true`, `false`, `1`, `0`, `yes`, `no`, `on`, or `off`; invalid values stop the
application with a clear error. When UAT mode is enabled, startup also stops if
debug is enabled, the secret is missing or weak, or allowed hosts are empty.

Before starting UAT, verify every hostname and origin in `.env`. The supplied
configuration uses one public HTTPS hostname. The reverse proxy sends `/api/`,
`/admin/`, `/health/`, and `/static/` to Django and sends all remaining paths
to Streamlit. If you deploy the services under different hostnames, update
`DJANGO_API_URL`, allowed hosts, CORS, CSRF, and the extension URL together.
The SQLite path must be on persistent storage and UAT should run as a single
Django application instance. Use PostgreSQL before running multiple instances.

Install, migrate, collect static files, and validate the deployment settings:

```powershell
pip install -r requirements.txt
python django_backend\manage.py migrate
python django_backend\manage.py collectstatic --noinput
python django_backend\manage.py check --deploy
```

From `django_backend`, run the Django API with Waitress instead of Django's
development server:

```powershell
waitress-serve --listen=127.0.0.1:8000 config.wsgi:application
```

From the repository root, run Streamlit behind the same trusted HTTPS reverse
proxy:

```powershell
streamlit run streamlit_app\app.py --server.address 127.0.0.1 --server.port 8501
```

The proxy should expose `https://mailforge.dev.acuvisor.com`, terminate TLS,
route the Django paths listed above to port 8000, and route other paths to
Streamlit on port 8501. Keep `DJANGO_TRUST_PROXY_HEADERS=true` only if the proxy
removes client-supplied forwarding headers and sets `X-Forwarded-Proto` itself.
Confirm `GET /health/` returns `{"status":"ok"}`.

The Chrome extension has its own switch because extension code cannot read the
server `.env` file. In `chrome_extension/config.js`, use `uat: true` for UAT or
`uat: false` for localhost, then reload the unpacked extension and the open
MailForge and Gmail tabs.

