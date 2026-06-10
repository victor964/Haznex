# Haznex — Railway Deployment Guide

This guide is for Victor and Hazel to deploy the Haznex Django application to [Railway](https://railway.app). The site is a single Django project — no separate frontend deployment.

---

## Quick checklist

1. Create a Railway project and connect this GitHub repository (root directory: repo root, not `backend/`).
2. Add the **PostgreSQL** plugin — Railway injects `DATABASE_URL` automatically. Do **not** hardcode database credentials.
3. Set all environment variables below in **Railway → Variables**.
4. Set `DJANGO_SETTINGS_MODULE=vhbridge.settings_production`.
5. Deploy. The `Procfile` runs migrations, collects static files, and starts Gunicorn.
6. Open a Railway shell and run `cd backend && python manage.py createsuperuser`.
7. In Django admin or shell, set `is_admin=True` on Victor and Hazel's `UserProfile` records.
8. Visit your Railway URL and test the full order flow.

---

## Required Railway environment variables

### Django core

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `DJANGO_SETTINGS_MODULE` | Tells Django to use production settings | Set manually | `vhbridge.settings_production` |
| `SECRET_KEY` | Django cryptographic signing key | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` | `django-insecure-abc123...` (use a long random value) |
| `DEBUG` | Debug mode — must be off in production | Set manually | `False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames Django will serve | Your Railway domain + custom domain when ready | `haznex.up.railway.app,haznex.co.ke` |
| `SITE_URL` | Public site URL for email links (no trailing slash) | Your live domain | `https://haznex.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origins allowed for form POSTs | Same as public URL(s) with `https://` | `https://haznex.up.railway.app,https://haznex.co.ke` |

### Database

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | **Auto-injected** when you add Railway PostgreSQL plugin | `postgresql://postgres:pass@containers-us-west-xxx.railway.app:5432/railway` |

> Railway sets `DATABASE_URL` automatically. The app parses it in `settings_production.py` via `dj-database-url`. You do **not** need to set `DB_NAME`, `DB_USER`, etc. separately unless you prefer manual config (not recommended).

Optional local-style vars (only if **not** using `DATABASE_URL` — not recommended on Railway):

| Variable | Example |
|----------|---------|
| `DB_NAME` | `railway` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | (from Railway Postgres credentials) |
| `DB_HOST` | `containers-us-west-xxx.railway.app` |
| `DB_PORT` | `5432` |

### Cloudinary (product images)

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account cloud name | [Cloudinary Console](https://cloudinary.com/console) → Dashboard | `dxyz123abc` |
| `CLOUDINARY_API_KEY` | API key | Cloudinary Console → API Keys | `123456789012345` |
| `CLOUDINARY_API_SECRET` | API secret | Cloudinary Console → API Keys | `abcdefghijklmnopqrstuvwxyz123` |

### M-Pesa (Daraja API)

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `MPESA_ENVIRONMENT` | Sandbox or production | [Safaricom Daraja Portal](https://developer.safaricom.co.ke) | `sandbox` or `production` |
| `MPESA_CONSUMER_KEY` | App consumer key | Daraja → My Apps → your app | `abc123...` |
| `MPESA_CONSUMER_SECRET` | App consumer secret | Daraja → My Apps → your app | `xyz789...` |
| `MPESA_SHORTCODE` | Paybill / till number | Daraja app credentials (sandbox: `174379`) | `174379` |
| `MPESA_PASSKEY` | Lipa Na M-Pesa Online passkey | Daraja app → Lipa Na M-Pesa Online | `bfb279f9aa9bdbcf...` |
| `MPESA_CALLBACK_URL` | HTTPS URL Safaricom POSTs STK results to | Your live domain + `/payments/callback/` | `https://haznex.up.railway.app/payments/callback/` |
| `MPESA_STK_ENABLED` | Enable automatic STK Push | Set `True` only when callback URL is live | `False` (start with manual confirm) |

### Email (Gmail SMTP)

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `EMAIL_HOST` | SMTP server | Gmail default | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | Gmail TLS port | `587` |
| `EMAIL_USE_TLS` | Use TLS | Set to true for Gmail | `True` |
| `EMAIL_HOST_USER` | Gmail address sending emails | Victor's Gmail | `victor@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail **App Password** (not account password) | [Google App Passwords](https://myaccount.google.com/apppasswords) | `abcd efgh ijkl mnop` |
| `DEFAULT_FROM_EMAIL` | From header in emails | Match Gmail address | `Haznex <victor@gmail.com>` |
| `EMAIL_NOTIFICATIONS_ENABLED` | Gate all status emails | Set `True` when SMTP is configured | `False` |

### Contact / WhatsApp

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `WHATSAPP_NUMBER` | WhatsApp chat button number (international format, no + prefix) | Your business WhatsApp number | `254712345678` |

### Pricing

| Variable | What it is | Where to get it | Example |
|----------|------------|-----------------|---------|
| `GBP_TO_KES_RATE` | Exchange rate for product price calculator | Current GBP→KES rate you want to use | `165.00` |

### Optional (CORS — only if calling API from external frontend)

| Variable | Example |
|----------|---------|
| `CORS_ALLOWED_ORIGINS` | `https://haznex.co.ke` |

---

## How deployment works

| File | Purpose |
|------|---------|
| [`Procfile`](Procfile) | Runs migrate, collectstatic (`--noinput`), then Gunicorn |
| [`railway.json`](railway.json) | Railway Nixpacks build config |
| [`runtime.txt`](runtime.txt) | Python version (`3.13.5`) |
| [`backend/vhbridge/settings_production.py`](backend/vhbridge/settings_production.py) | Production overrides (SSL, HSTS, WhiteNoise, `DATABASE_URL`) |

Static files are served by **WhiteNoise** on Railway. Media (product images) are stored on **Cloudinary** — no separate media bucket needed.

`collectstatic` runs at **build time** and again at **start** (with `--clear`) into `backend/staticfiles/`. It uses `vhbridge.settings` so it does not require `DATABASE_URL`. If deploy logs show `No directory at: .../staticfiles/`, push the latest `railway.json` and redeploy — you should see `173 static files copied` in the build or deploy logs.

---

## Post-deploy steps

### Create admin users

```bash
cd backend
python manage.py createsuperuser
```

Then in Django shell or `/admin/`:

```python
from django.contrib.auth.models import User
user = User.objects.get(username="victor")
user.profile.is_admin = True
user.profile.save()
```

Repeat for Hazel's account.

### Enable M-Pesa STK Push (when ready)

1. Deploy with a public HTTPS URL.
2. Register callback URL in Daraja: `https://YOUR-DOMAIN/payments/callback/`
3. Set `MPESA_CALLBACK_URL` to that URL.
4. Set `MPESA_STK_ENABLED=True`.
5. Redeploy and test a small payment in sandbox first.

### Enable email notifications

1. Generate a Gmail App Password for Victor's account.
2. Set `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL`.
3. Set `EMAIL_NOTIFICATIONS_ENABLED=True`.
4. Redeploy and trigger a test order status change.

---

## Custom domain (after you purchase one)

Domain setup is **not** automated in code. After buying a domain (e.g. `haznex.co.ke`):

1. In Railway → **Settings → Domains**, add your custom domain.
2. At your domain registrar, add the CNAME record Railway provides.
3. Update these Railway variables:
   - `ALLOWED_HOSTS` — add `haznex.co.ke`
   - `SITE_URL` — `https://haznex.co.ke`
   - `CSRF_TRUSTED_ORIGINS` — `https://haznex.co.ke`
   - `MPESA_CALLBACK_URL` — `https://haznex.co.ke/payments/callback/`
4. Redeploy and verify HTTPS works.

---

## Useful commands

```bash
# Local production check (set env vars first)
cd backend
set DJANGO_SETTINGS_MODULE=vhbridge.settings_production
set DATABASE_URL=postgresql://...
set ALLOWED_HOSTS=localhost
set CSRF_TRUSTED_ORIGINS=https://localhost
python manage.py check --deploy

# Run tests
python manage.py test store orders payments

# Collect static locally (production settings)
python manage.py collectstatic --noinput
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| `DisallowedHost` | Domain not in `ALLOWED_HOSTS` | Add Railway URL and custom domain |
| CSRF verification failed | Missing `CSRF_TRUSTED_ORIGINS` | Add `https://` origin |
| Static files 404 | collectstatic not run | Redeploy; check Procfile logs |
| Images not uploading | Cloudinary vars missing | Set all three `CLOUDINARY_*` vars |
| STK Push fails | Callback not HTTPS / not reachable | Use ngrok for testing; set live URL for production |
| Emails not sending | App Password wrong or gate off | Check `EMAIL_NOTIFICATIONS_ENABLED=True` |

---

Built by Vynex (Victor Maina Njenga) & Hazel Mburu · Haznex EX-UK Products
