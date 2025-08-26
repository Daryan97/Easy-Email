# Security Policy

## 🐍 Python Version
This project is developed and tested with **Python 3.12.4**.  
The minimum supported version is **Python 3.7.4**.  
Older versions of Python (<3.7.4) are not supported.

---

## 📦 Supported Versions

Currently, only the **latest release (main branch)** is supported with security updates.  

| Component              | Supported          |
| ---------------------- | ------------------ |
| Main branch            | :white_check_mark: |
| Old branches           | :x:                |
| Python 3.12.4 (tested) | :white_check_mark: |
| Python ≥3.7.4          | :white_check_mark: |
| Python <3.7.4          | :x:                |

---

## 🔒 Dependencies

The project relies on the following key dependencies, which are regularly updated for security patches:

- `httpx==0.27.0`
- `PyJWT==2.9.0`
- `alembic==1.13.2`
- `Flask==3.0.3`
- `Flask_JWT_Extended==4.6.0`
- `flask_mail==0.10.0`
- `Flask_Migrate==4.0.7`
- `flask_restx==1.3.0`
- `flask_sqlalchemy==3.1.1`
- `pymysql==1.1.1`
- `python-dotenv==1.0.1`
- `SQLAlchemy==2.0.31`
- `Werkzeug==3.1.3`
- `openai==1.42.0`
- `email-validator==2.2.0`
- `flask-cors==5.0.1`
- `gunicorn==23.0.0`
- `gevent==24.11.1`
- `fernet==1.0.1`
- `google-auth-oauthlib==1.2.1`
- `google-auth-httplib2==0.2.0`
- `google-api-python-client==2.149.0`
- `msal==1.31.0`
- `psycopg2-binary==2.9.10`
- `redis==5.1.1`
- `Flask-Limiter==3.8.0`
- `BeautifulSoup4==4.12.3`

### Pinned by Security (Snyk)
The following packages are pinned specifically to avoid known vulnerabilities:
- `anyio>=4.4.0`
- `h11>=0.16.0`
- `protobuf>=4.25.8`
- `requests>=2.32.4`
- `urllib3>=2.5.0`
- `zipp>=3.19.1`

---

## 🛡️ Reporting a Vulnerability

If you discover a security vulnerability in Easy-Email:

1. **Do not open a public issue.**  
   Instead, please report it responsibly.

2. Submit a detailed report via the [GitHub Issues page](https://github.com/Daryan97/Easy-Email/issues).

3. Please include:
   - A clear description of the vulnerability.  
   - Steps to reproduce the issue (if possible).  
   - Potential impact on the system.  
   - Suggested fix or mitigation (if you have one).  

4. **Response expectations:**  
   - Acknowledgment of your report within **72 hours**.  
   - Initial assessment within **7 days**.  
   - Regular updates on the status of your report.  

If the vulnerability is valid, it will be prioritized for patching in the next release cycle. If declined, you will receive an explanation.

---

## 🙏 Responsible Disclosure

We encourage researchers and contributors to report vulnerabilities responsibly and allow time for fixes before public disclosure.
