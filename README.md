<div align="center">

# Haznex

### EX-UK Products — Sourced in the UK, Delivered to Kenya

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)](https://railway.app)
[![Cloudinary](https://img.shields.io/badge/Media-Cloudinary-3448C5?style=flat-square&logo=cloudinary&logoColor=white)](https://cloudinary.com)
[![License](https://img.shields.io/badge/License-MIT-gold?style=flat-square)](LICENSE)

**A full-stack dropshipping platform bridging UK markets to Kenyan buyers.**
Browse genuine EX-UK products, pay via M-Pesa, and track your order every step of the way.

[Live Site](https://haznex.up.railway.app) · [Admin Panel](https://haznex.up.railway.app/haznex-admin/) · [Report a Bug](https://github.com/vynex/haznex/issues)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Business Model](#business-model)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Built By](#built-by)

---

## Overview

**Haznex** is a production-grade dropshipping platform built for a two-person cross-border operation between the UK and Kenya. It solves a real market problem: Kenyan buyers cannot easily access quality products from UK platforms like Facebook Marketplace at fair prices.

The platform handles the complete order lifecycle:

1. Admins source products from the UK (via Facebook Marketplace or local stock) and list them with a calculated landed price
2. Clients browse, order, and pay via M-Pesa
3. The UK-side partner picks and ships the item
4. The Kenya-side partner handles local delivery
5. Clients track their order through every stage in real time

Haznex is a **Vynex** product, built by Victor Maina Njenga in collaboration with Hazel Mburu.

---

## Features

### Client-Facing Storefront

- **Captivating homepage** with GSAP-powered word-by-word hero animation, trust indicators, and featured product grid
- **Product catalogue** with search, condition filters (New, Used, Refurbished), and source filters (EX-UK, Local)
- **Product detail pages** with image gallery crossfade, full description, condition badge, and live shipping cost calculator
- **Shipping options** — clients choose between air freight (faster) or sea freight (more affordable), with prices calculated from product weight
- **Client registration and login** with automatic UserProfile creation
- **Order placement flow** with live total calculation and delivery address capture
- **M-Pesa payment** via Safaricom Daraja API — STK Push prompt or manual confirmation fallback
- **Order tracking timeline** with GSAP sequential animation, admin notes per stage, and estimated delivery range
- **My Orders dashboard** with color-coded status badges and last-updated timestamps
- **Email notifications** on every order status change via Gmail SMTP

### Admin Panel (Haznex Admin)

- **Secure dual-admin access** — Victor and Hazel both have independent admin accounts with equal rights
- **Facebook Marketplace fetcher** — paste a listing URL to auto-extract title, description, images, and price (with full manual fallback)
- **Price calculator wizard** — input UK price, sourcing fee, shipping cost, logistics, and profit margin. Final KES price is calculated live in JavaScript and validated server-side
- **Product management** — create, edit, activate/deactivate, and delete listings
- **Cloudinary image upload** with multi-image support and primary image selection
- **Order management** with status filters, stale-order highlighting (orders untouched for 3+ days), and quick filter tabs
- **Order status update tool** — move orders through the full status flow with admin notes
- **Payment confirmation** — manual payment confirm tool for when STK Push is not configured
- **Order cancellation** with client notification via email
- **Enhanced dashboard** — orders needing action grouped by status, recent activity feed, and key stats

### Order Status Flow

```
Payment Pending  →  Payment Confirmed  →  Sourcing Item  →  Shipped from UK
      →  In Transit  →  Arrived in Kenya  →  Out for Delivery  →  Completed
```

Cancellation is possible from any non-terminal stage.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.x + Django REST Framework |
| Database | PostgreSQL 16 |
| Image Storage | Cloudinary |
| Frontend | Django Templates + Tailwind CSS + GSAP 3.12 |
| Payment | Safaricom Daraja API (M-Pesa STK Push) |
| Email | Django EmailMultiAlternatives via Gmail SMTP |
| Web Server | Gunicorn + WhiteNoise (static files) |
| Deployment | Railway |
| Version Control | Git + GitHub |

---

## Project Architecture

```
haznex/
├── backend/
│   ├── vhbridge/               # Django project — settings, root URLs, WSGI
│   │   ├── settings.py         # Development settings
│   │   └── settings_production.py  # Production overrides (SSL, WhiteNoise, dj-database-url)
│   ├── store/                  # Products — models, views, storefront templates
│   │   ├── models.py           # Product, ProductImage, PriceBreakdown, ShippingOption
│   │   ├── choices.py          # OrderStatus, ProductCondition, SourceType, ORDER_STATUS_FLOW
│   │   └── templates/store/    # Homepage, product list, product detail, base template
│   ├── orders/                 # Orders — models, views, tracking, email notifications
│   │   ├── models.py           # Order, OrderStatusUpdate
│   │   ├── signals.py          # post_save signal triggers email on status change
│   │   ├── email_notifications.py  # Status-specific email service
│   │   └── templates/orders/   # Order tracking, My Orders, email templates
│   ├── accounts/               # Client auth — registration, login, UserProfile
│   │   └── models.py           # UserProfile (extends User, adds phone, is_admin)
│   ├── admin_panel/            # Haznex admin — dashboard, product wizard, order tools
│   │   ├── views/              # Auth, dashboard, products, orders (split by concern)
│   │   └── templates/admin_panel/  # Admin UI templates
│   ├── payments/               # M-Pesa integration
│   │   ├── models.py           # Payment (tracks STK Push state, receipt, manual confirm)
│   │   └── daraja.py           # DarajaAPI service class (token, STK Push, callback parser)
│   └── manage.py
├── frontend/                   # Tailwind CSS build pipeline
├── Procfile                    # Railway: migrate + collectstatic + gunicorn
├── railway.json                # Railway Nixpacks config
├── runtime.txt                 # Python version pin
├── requirements.txt
└── DEPLOYMENT.md               # Full deployment reference for Victor and Hazel
```

### Key Design Decisions

**Fat models, thin views.** Business logic lives in models and service classes (`daraja.py`, `email_notifications.py`), not in views.

**Atomic transactions.** Product creation (Product + PriceBreakdown + ProductImages) and order creation both use `transaction.atomic()` to prevent partial saves.

**Signal-driven notifications.** A `post_save` signal on `OrderStatusUpdate` (created=True only) triggers emails, keeping the model's `save()` method clean and notifications decoupled.

**Price integrity.** `PriceBreakdown.clean()` enforces that `final_client_price` always equals the exact sum of the four component costs. The calculator validates this both client-side (live JavaScript) and server-side (Django model validation).

**Admin separation.** The Haznex admin panel at `/haznex-admin/` is completely separate from Django's built-in `/admin/`. Access is gated by `UserProfile.is_admin = True` on every view via a custom mixin.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- A Cloudinary account (free tier is sufficient)
- Git

### Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/vynex/haznex.git
cd haznex
```

**2. Create and activate a virtual environment**

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and fill in the required values. At minimum for local development:

```env
SECRET_KEY=your-local-dev-secret-key
DEBUG=True
DB_NAME=vhbridge
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
GBP_TO_KES_RATE=165.00
MPESA_STK_ENABLED=False
EMAIL_NOTIFICATIONS_ENABLED=False
```

**5. Create the PostgreSQL database**

```sql
CREATE DATABASE vhbridge;
```

**6. Run migrations and create a superuser**

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

**7. Set your account as a Haznex admin**

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
user = User.objects.get(username="your-username")
user.profile.is_admin = True
user.profile.save()
```

**8. Start the development server**

```bash
python manage.py runserver
```

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Client storefront |
| `http://127.0.0.1:8000/haznex-admin/` | Haznex admin panel |
| `http://127.0.0.1:8000/admin/` | Django built-in admin |

---

## Environment Variables

A full reference is in [DEPLOYMENT.md](DEPLOYMENT.md). Key variables:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `True` for development, `False` for production |
| `DATABASE_URL` | Production | Auto-injected by Railway PostgreSQL plugin |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary account identifier |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary API secret |
| `GBP_TO_KES_RATE` | Yes | Exchange rate used in price calculator |
| `MPESA_CONSUMER_KEY` | For STK Push | Daraja app consumer key |
| `MPESA_CONSUMER_SECRET` | For STK Push | Daraja app consumer secret |
| `MPESA_STK_ENABLED` | Yes | `True` to enable automatic STK Push |
| `EMAIL_HOST_USER` | For emails | Gmail address for status notifications |
| `EMAIL_HOST_PASSWORD` | For emails | Gmail App Password (not account password) |
| `EMAIL_NOTIFICATIONS_ENABLED` | Yes | `True` to send order status emails |

---

## Deployment

Haznex is deployed on [Railway](https://railway.app) with a managed PostgreSQL database.

**Quick deploy steps:**

1. Fork this repository
2. Create a new Railway project and connect the GitHub repository
3. Add the Railway PostgreSQL plugin
4. Set environment variables in Railway (see [DEPLOYMENT.md](DEPLOYMENT.md) for the full list)
5. Set `DJANGO_SETTINGS_MODULE=vhbridge.settings_production`
6. Deploy — Railway runs the `Procfile` automatically:
   ```
   migrate → collectstatic → gunicorn
   ```
7. Open a Railway shell and create admin users

The `Procfile`, `railway.json`, and `runtime.txt` in the project root handle all build and start configuration automatically.

---

## Business Model

Haznex operates as a **demand-driven dropshipping** platform. No inventory is held. Orders are fulfilled only after payment is confirmed.

**How an order works:**

```
Client places order
        ↓
Client pays via M-Pesa (STK Push or manual confirm)
        ↓
Admin confirms payment — order becomes active
        ↓
UK partner (Hazel) sources item from Facebook Marketplace or local UK seller
        ↓
Item is shipped to Kenya via air or sea freight
        ↓
Kenya partner (Victor) receives item and arranges local delivery
        ↓
Item delivered to client — order marked Completed
```

**Price formula:**

```
Final client price (KES) = UK item price + sourcing fee + shipping cost
                         + transport and logistics + profit margin
```

Local delivery to the client is quoted separately after the item arrives in Kenya.

---

## Screenshots

> Screenshots coming soon. The live site is available at [haznex.up.railway.app](https://haznex.up.railway.app)

---

## Contributing

This is a private commercial project. The repository is public for portfolio and reference purposes.

If you find a bug or security issue, please open an issue or contact Victor directly.

---

## Built By

**Haznex** is a product of [Vynex](https://github.com/vynex).

| | |
|---|---|
| **Victor Maina Njenga** | Developer and Kenya operations — Vynex, Murang'a, Kenya |
| **Hazel Mburu** | UK operations and product sourcing — United Kingdom |

---

<div align="center">

Built with care by Vynex · Murang'a, Kenya

*Bridging UK Markets to Your Doorstep*

</div>
