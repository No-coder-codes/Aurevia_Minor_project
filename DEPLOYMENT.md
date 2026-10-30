# NexusFlow College Operations & Academic Management SaaS
## Production Deployment & Operations Guide

---

## 1. Architecture Overview

NexusFlow is a modern, modular Django-based SaaS platform engineered for multi-tenant higher education institutions. The system models an entire university ecosystem—including institutional leadership (President, Provost, Registrar), Schools, Academic Departments, Degree Programmes, Class Divisions, Teaching Allocations, Student Rosters, Residential Hostels, Facilities/IT Operations, and a Cross-Functional Admissions Pipeline featuring dual-reporting (Registrar operations + Faculty academic evaluation).

```
                 Internet / Campus WAN
                           │
                           ▼
                    [Nginx 1.22+]
            (TLS/SSL Termination + Static Files)
                           │
                           ▼ Unix Domain Socket / HTTP
                 [Gunicorn WSGI Workers]
              (NexusFlow Django Application)
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
   [PostgreSQL 14+]               [Local / S3 Media]
 (ACID Relational Storage)     (Student/App Documents)
```

---

## 2. Server Prerequisites

- **Operating System**: Ubuntu 22.04 LTS or Debian 12
- **Python**: Python 3.11+
- **Database**: PostgreSQL 14+
- **Reverse Proxy**: Nginx with HTTP/2 and Certbot (Let's Encrypt SSL)
- **Process Manager**: Systemd (`systemctl`)
- **Hardware Minimum**: 2 vCPU, 4GB RAM, 25GB SSD

---

## 3. Production Installation Step-by-Step

### 3.1 Base System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl git
```

### 3.2 PostgreSQL Database Provisioning

```bash
sudo -u postgres psql
```

Execute SQL commands:
```sql
CREATE DATABASE nexusflow_db;
CREATE USER nexusflow_admin WITH PASSWORD 'YourStrongDbPassword123!';
ALTER ROLE nexusflow_admin SET client_encoding TO 'utf8';
ALTER ROLE nexusflow_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE nexusflow_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nexusflow_db TO nexusflow_admin;
\q
```

### 3.3 Application Setup & Virtual Environment

```bash
# Clone or copy application to production path
sudo mkdir -p /var/www/nexusflow
sudo chown -R $USER:$USER /var/www/nexusflow
cd /var/www/nexusflow

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3.4 Production Environment Configuration

Copy the environment template and configure production values:
```bash
cp .env.example .env
nano .env
```

Ensure the following variables are configured:
```ini
DEBUG=False
SECRET_KEY=replace-with-a-random-50-character-secret-key-here
ALLOWED_HOSTS=nexusflow.yourcampus.edu,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=nexusflow_db
DB_USER=nexusflow_admin
DB_PASSWORD=YourStrongDbPassword123!
DB_HOST=127.0.0.1
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://nexusflow.yourcampus.edu
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

### 3.5 Database Migrations, Demo Seeding & Static Collection

```bash
# Run database schema migrations
python manage.py migrate

# Seed synthetic university demo data
python manage.py seed_demo_data

# Collect static assets
python manage.py collectstatic --noinput
```

---

## 4. Gunicorn Systemd Service Setup

Create the systemd service file:
```bash
sudo nano /etc/systemd/system/nexusflow.service
```

Add configuration:
```ini
[Unit]
Description=NexusFlow College Operations SaaS Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/nexusflow
ExecStart=/var/www/nexusflow/venv/bin/gunicorn \
          --access-logfile - \
          --error-logfile - \
          --workers 3 \
          --bind unix:/run/nexusflow.sock \
          management_system.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl start nexusflow
sudo systemctl enable nexusflow
sudo systemctl status nexusflow
```

---

## 5. Nginx Configuration with SSL

Create Nginx site configuration:
```bash
sudo nano /etc/nginx/sites-available/nexusflow
```

Paste configuration:
```nginx
server {
    listen 80;
    server_name nexusflow.yourcampus.edu;

    client_max_body_size 25M;

    # Static files served directly by Nginx
    location /static/ {
        alias /var/www/nexusflow/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Uploaded documents and media
    location /media/ {
        alias /var/www/nexusflow/media/;
        expires 7d;
    }

    # Proxy all application requests to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/nexusflow.sock;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/nexusflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Obtain free SSL certificate via Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d nexusflow.yourcampus.edu
```

---

## 6. Daily Operations & Maintenance

### 6.1 Automated Daily Database Backup
Add to root crontab (`sudo crontab -e`):
```cron
0 2 * * * pg_dump -U nexusflow_admin -h 127.0.0.1 nexusflow_db | gzip > /var/backups/nexusflow/db_$(date +\%Y\%m\%d).sql.gz
```

### 6.2 Health Checks & Logs
- **Gunicorn Logs**: `journalctl -u nexusflow -f`
- **Nginx Error Logs**: `tail -f /var/log/nginx/error.log`
- **Django System Check**: `python manage.py check --deploy`

---

## 7. Demo Accounts & Credentials

The `seed_demo_data` command provisions the following demonstration accounts (default password: `NexusFlow123!`):

| Role | Username | Full Name | Access Level |
|---|---|---|---|
| **President** | `president_vance` | Dr. Eleanor Vance | Full Institutional Overview (All Schools, Operations & Pipeline) |
| **Provost** | `provost_pendelton` | Dr. Arthur Pendelton | Academic Leadership, Admissions Final Approvals |
| **Registrar** | `registrar_hayes` | Dr. Margaret Hayes | Administrative Directory, Hostels, Admissions Operations |
| **Dean (Engineering)** | `dean_chen` | Dr. Robert Chen | School of Engineering, Academic Department Allocations, Academic Reviews |
| **HoD (Computer Science)**| `hod_cse` | Dr. Vikram Deshmukh | CSE Department, Teaching Allocations, Curriculum |
| **Faculty Member** | `prof_turing` | Prof. Alan Turing | Assigned Teaching Modules (CS501 Operating Systems) |
| **Class Rep (CR)** | `student_alice` | Alice Zhang | Class Representative Portal (BT-CSE Sem 5 Sec A) |
| **Hostel Warden** | `warden_mens` | Col. James Rhodes | Mandela Boys' Residence Hall Facility Management & Tasks |
| **Admissions Lead** | `admissions_officer` | Nyota Uhura | Admissions Intake & Administrative Verification |
