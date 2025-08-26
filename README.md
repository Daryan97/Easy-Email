# Easy-Email

Easy-Email is an AI-powered assistant that helps you generate, edit, and send professional emails.  
It leverages **Cloudflare Workers AI** for content generation and integrates with **Gmail, Outlook, and other email APIs** to send and manage emails directly in the app. With features like smart replies, contact management, OAuth account linking, and AI-driven drafting, Easy-Email saves time and boosts productivity.

---

## 📑 Contents
- [Features](#-features)  
- [Tech Stack](#-tech-stack)  
- [Installation](#-installation)  
- [Configuration](#-configuration)  
- [Google API Setup (Gmail)](#-google-api-setup-gmail)  
- [Microsoft API Setup (Outlook)](#-microsoft-api-setup-outlook)  
- [Usage](#-usage)  
- [Troubleshooting](#-troubleshooting)  
- [License](#-license)  

---

## ✨ Features
- Generate and edit professional emails with AI.
- Smart Reply: AI-generated replies based on received emails.
- Gmail & Outlook integration via OAuth 2.0.
- Contact management (create, update, delete, view).
- Redis-backed rate limiting.
- Secure authentication and encryption (e.g., Fernet for secrets).
- Optional SMTP for OTP delivery.

---

## 🧰 Tech Stack
- **Backend:** Python (Flask / Flask-RESTx), SQLAlchemy
- **Database:** PostgreSQL
- **AI:** Cloudflare Workers AI
- **Auth & APIs:** Google OAuth (Gmail/People), Microsoft Entra ID (Outlook/Microsoft Graph)
- **Cache/Rate limit:** Redis
- **Other:** Docker, Nginx Proxy (deployment)

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Daryan97/Easy-Email
   cd Easy-Email
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Redis** (example using Docker Compose)
   ```yaml
   version: '3'
   services:
     redis:
       image: redis
       container_name: easy-email-redis
       ports:
         - "6379:6379"
       command: ["redis-server", "--requirepass", "your_password"]
   ```
   Start it:
   ```bash
   docker compose up -d
   ```

4. **Copy and edit environment variables**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and fill in the required values (see [Configuration](#configuration)).

5. **Create the PostgreSQL database**
   Ensure PostgreSQL is running and create a DB whose name matches your `.env`.

6. **Run the development server**
   ```bash
   flask run
   ```
   By default the app runs at `http://127.0.0.1:5000/`.

---

## 🔧 Configuration

Update these keys in your `.env` (names are examples—match your codebase if it uses different names):

```dotenv
# Flask / Security
FLASK_ENV=development
SECRET_KEY=replace_me
FERNET_KEY=32_byte_base64_key_here

# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/easy_email

# Redis
REDIS_URL=redis://:your_password@127.0.0.1:6379/0

# Cloudflare Workers AI
WORKERS_AI_ACCOUNT_ID=your_account_id
WORKERS_AI_API_TOKEN=your_api_token
WORKERS_AI_MODEL=@cf/meta/llama-3.1-8b-instruct  # example

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/google/callback
GOOGLE_SCOPES=email profile openid https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly
# (optional) add People API scope if you fetch contacts:
# https://www.googleapis.com/auth/contacts.readonly

# Microsoft OAuth (Entra ID / Azure App Registration)
MS_CLIENT_ID=...
MS_CLIENT_SECRET=...
MS_TENANT_ID=common
MS_REDIRECT_URI=http://127.0.0.1:5000/auth/microsoft/callback
MS_SCOPES=offline_access Mail.ReadWrite Mail.Send User.Read User.ReadBasic.All

# SMTP (optional, e.g., OTP only)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=no-reply@example.com
SMTP_PASSWORD=...
SMTP_TLS=true
```

> **Note:** Make sure your `/auth/google/callback` and `/auth/microsoft/callback` routes exist in the app. If your routes differ, update the redirect URIs and any OAuth config accordingly.

---

## 🔐 Google API Setup (Gmail)

Follow these steps in **Google Cloud Console**:

1. **Create a project** (or use an existing one).  
2. **Enable APIs** → *APIs & Services* → *Enable APIs and Services*:  
   - **Gmail API**
   - **People API** (only if you need contacts)
3. **Configure OAuth consent screen**:  
   - User Type: *External* (for most use-cases) or *Internal* for Workspace.  
   - Fill in app info, scopes (you can add during credential creation too), and **add test users** if the app is not published.  
4. **Create OAuth 2.0 Credentials** → *Credentials* → *Create Credentials* → *OAuth client ID*:  
   - Application type: **Web application**  
   - **Authorized redirect URIs**: add your app callback, e.g.  
     - `http://127.0.0.1:5000/auth/google/callback`
     - `https://your-domain.com/auth/google/callback`
5. **Copy the Client ID and Client Secret** into your `.env`.
6. **Use the following scopes** (as requested):  
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/gmail.send` (Send Email)
   - `https://www.googleapis.com/auth/gmail.readonly` (Read Email)

> If you later need full Gmail write access (labels, drafts), you may add broader scopes, but start with least privilege.

---

## 🟦 Microsoft API Setup (Outlook / Microsoft Graph)

Steps in **Azure Portal** → *Microsoft Entra ID*:

1. **App registrations** → *New registration*:  
   - Name your app, choose *Accounts in any organizational directory and personal Microsoft accounts* (or as needed).
2. After creation, note **Application (client) ID** and **Directory (tenant) ID**.  
3. **Certificates & secrets** → *Client secrets* → *New client secret* → copy the **secret value** (once).  
4. **Authentication** → add **Redirect URIs** (Web):  
   - `http://127.0.0.1:5000/auth/microsoft/callback`
   - `https://your-domain.com/auth/microsoft/callback`  
   Enable **ID tokens** if you rely on OpenID Connect.
5. **API permissions** → *Microsoft Graph* → *Delegated permissions* → add the scopes you asked for:  
   - `Mail.ReadWrite`
   - `Mail.Send`
   - `offline_access`
   - `User.Read`
   - `User.ReadBasic.All`
   Click **Grant admin consent** (if required by your tenant).  
6. Put **MS_CLIENT_ID**, **MS_CLIENT_SECRET**, **MS_TENANT_ID** (or `common`), **MS_REDIRECT_URI**, and **MS_SCOPES** in `.env`.

> For personal Microsoft accounts, `MS_TENANT_ID=common` works. For single-tenant orgs, use the specific tenant ID.

---

## 🚀 Usage
1. Start the backend (`flask run`).  
2. Visit the app in your browser.  
3. Link your **Google** or **Microsoft** account via the Connect/Link button.  
4. Draft a new email with AI or open an existing email to **Smart Reply**.  
5. Send directly through Gmail/Outlook APIs.

---

## 🧩 Troubleshooting

- **invalid_client / redirect_uri_mismatch**  
  Ensure the redirect URI in your provider console **exactly** matches the one used by your app and `.env`.
- **Google test users blocked**  
  Add your email to **Test users** on the OAuth consent screen until the app is published.
- **Insufficient permissions / 403**  
  Verify that scopes requested by the app match those configured and granted in the provider.
- **Rate limiting**  
  Confirm `REDIS_URL` is correct and the Redis server is reachable with the configured password.
- **SMTP OTP not delivered**  
  Check SMTP credentials and TLS settings; some providers require “App Passwords”.

---

## 📜 License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
