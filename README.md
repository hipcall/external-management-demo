# Hipcall External Management Demo

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is a basic dummy program that demonstrates how [**Hipcall External Management**](https://use.hipcall.com.tr/portal/customer-service/contents/hipcall/gelis%CC%A7tirme-arac%CC%A7lar%C4%B1/hipcall-harici-yo%CC%88netim-external-management-nedir-ve-nas%C4%B1l-kullan%C4%B1l%C4%B1r/) features communicate with different systems and how they can be used. This program should be considered as the customer’s own software that integrates with Hipcall External Management and can be further developed according to their specific needs.

---

## 🚀 Scenarios & Features

The project demonstrates three core interaction scenarios commonly used in telephony integrations:

1.  **PIN Query (PIN Sorgulama):**
    *   Authenticates users by requesting a 4-digit PIN code via IVR.
    *   Matches the caller's phone number with the database and verifies the entered PIN.
    *   Plays success or error messages based on the result.

2.  **External Routing (Dış Yönlendirme):**
    *   Demonstrates the `dial` action by routing the call to an external phone number.
    *   The destination number can be dynamically updated via the management settings.

3.  **Internal Routing (İç Yönlendirme):**
    *   Demonstrates the `connect` action by routing the call to a specific internal extension.
    *   The target extension can be configured through the web interface.

---

## 🛠 Usage & Administration

The application provides a web-based dashboard for managing the system:

*   **User Management & PIN Query:** Add, edit, or delete user records. For **Scenario 1**, the caller's phone number must exist in this table. The caller will be prompted for their `pin_code`. If the entered PIN matches the customer's PIN, a success message plays; otherwise, an error message plays.
*   **Active Routing Settings (Settings Menu):** You can define multiple target phone numbers and extensions from the settings interface. The active choices selected via checkboxes here dictate the destination for routing scenarios:
    *   **Active Dial Number:** Defines the destination phone number used in **Scenario 2** (External Routing). The number marked as active is the one the Hipcall system will `dial`.
    *   **Active Extension:** Defines the target internal extension used in **Scenario 3** (Internal Routing). The extension marked as active is the one the Hipcall system will `connect` the call to.
*   **Log Tracking:** Monitor real-time logs of the webhook POST requests coming from the Hipcall Ingress API. You can see the full request body (caller info, digits pressed, etc.) and the JSON sequence response returned by our dummy system.

---

## 📂 Project Structure

```text
user_management_system/
├── app.py              # Main Flask application (API & Web Routes)
├── init_db.py          # Database initialization and seeding script
├── entrypoint.sh       # Docker entrypoint script (Restores DB from seed)
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker Compose orchestration
├── requirements.txt    # Python dependencies
├── data/               # Persistent storage for SQLite database
│   ├── database.db     # Active SQLite database
│   └── database.db.seed # Seed file for database resets
├── static/             # Static assets (CSS, JS, and Audio files)
│   └── audio/          # MP3 files used for IVR responses
└── templates/          # HTML templates for the dashboard
```

---

## ⚙️ Getting Started

### Prerequisites
- Docker & Docker Compose (Recommended)
- Python 3.8+ (For local development)

### Running with Docker

```bash
docker-compose up --build
```
The application will be accessible at `http://localhost:5005`.

**Default Login:**
- **Username:** `admin`
- **Password:** `admin123`

### Using External Management in Hipcall
You can create a new external management by clicking **Settings > External Managements** in the top right corner.
The endpoint used for this dummy application is: `/api/external/hipcall-ingress`



