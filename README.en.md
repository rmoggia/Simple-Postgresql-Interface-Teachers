# PG Admin Lite

[![🇮🇹 Italiano](https://img.shields.io/badge/🇮🇹-Italiano-green?style=flat-square)](README.md)
[![🇬🇧 English](https://img.shields.io/badge/🇬🇧-English-blue?style=flat-square)](README.en.md)

A lightweight web interface for PostgreSQL built with Flask and psycopg2.

## Requirements

- Python 3.8+
- PostgreSQL accessible over the network

## Installation

```bash
# 1. Enter the project folder
cd pg_admin_lite

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
python app.py
```

Open your browser at: **http://localhost:5000**

## Running with Docker

```bash
# Start both the app and PostgreSQL
docker compose up --build
```

Open your browser at: **http://localhost:5000**
In the login form use **`postgres`** as the host (container name, not `localhost`).

To stop: `docker compose down`
To stop and remove DB data: `docker compose down -v`
To follow logs: `docker compose logs -f`

## Features

| Section | Description |
|---------|-------------|
| **Login** | Connect using host, port, database, user and password |
| **Dashboard** | List of schemas and tables |
| **Table Data** | Paginated data view with column sorting |
| **Insert Row** | Form to add new records |
| **Edit Row** | Inline editing of an existing record |
| **Delete Row** | Row removal with confirmation prompt |
| **SQL Query** | Free SQL editor — Ctrl+Enter to execute |
| **Structure** | Column details, types, PKs + DDL editor |

## Security Notes

- DB credentials are stored only in the Flask session (in memory), never on disk
- Change `SECRET_KEY` in `config.py` (or in `.env`) before deploying to production
- Do not expose this application to the internet without additional authentication

## Project Structure

```
pg_admin_lite/
├── app.py              # Flask application, routes
├── db.py               # PostgreSQL connection and query management
├── config.py           # App configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                # Environment variables (DB credentials, secret key)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── table_view.html
│   ├── row_form.html
│   ├── query.html
│   └── structure.html
└── static/
    └── style.css
```
