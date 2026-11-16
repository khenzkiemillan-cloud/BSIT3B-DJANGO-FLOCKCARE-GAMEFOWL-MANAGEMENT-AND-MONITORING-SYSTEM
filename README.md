# FlockCare — Gamefowl Management & Monitoring System

Django application for tracking gamefowl flock members, health schedules,
fight records, breeding pens, and medicines.

## Requirements

- Python 3.11+
- SQLite (default) or MySQL 8+
- See `requirements.txt`

## Local development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Optional: copy the example environment file and edit it
cp .env.example .env        # Windows: copy .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Open http://127.0.0.1:8000/.

## Server deployment

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file (or set the variables in your process manager):

   ```env
   SECRET_KEY=replace-with-a-long-random-value
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   CSRF_TRUSTED_ORIGINS=https://your-domain.com
   USE_SQLITE=False
   USE_MYSQL=True
   DB_NAME=flockcare
   DB_USER=flockcare_user
   DB_PASSWORD=strong-password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

   Set `USE_HTTPS=True` when the site is served over HTTPS.

3. Apply migrations and collect static files:

   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. Start the WSGI server with Gunicorn:

   ```bash
   gunicorn --bind 0.0.0.0:8000 --workers 3 mysite.wsgi:application
   ```

   WhiteNoise is included so Gunicorn can serve the collected static files
   without an extra web-server rule.

## Docker

```bash
docker compose up --build
```

The compose setup starts MySQL and the Django app on port 8000. Change the
default credentials in `docker-compose.yml` before using it in production.

## Tests

```bash
python manage.py test
```

Tests automatically use an in-memory SQLite database.
