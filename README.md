# FlockCare — Gamefowl Management & Monitoring System

Django application for tracking gamefowl flock members, health schedules,
fight and weight records, breeding pens, medicines, and flock expenses.

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
python manage.py seed_data        # optional: demo flock, medicines, and expenses
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Open http://127.0.0.1:8000/.

The SQLite database (`db.sqlite3`) is not tracked in Git. After cloning,
create it with `python manage.py migrate` and optionally load the demo
records with `python manage.py seed_data`.

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

## Implementation status

The current build covers flock profiling, health and vaccination schedules,
medicine cabinet inventory, breeding and pedigree records, fight and weight
logs, and per-flock-member expense tracking. The earlier conditioning tracker
and the separate finance/sales pages were retired in favor of the expense
tracker. Restocking a medicine can optionally create a matching Medicine
expense, using either the receipt total or the stored cost per unit.

## Concept paper

BSIT Class Project Concept Paper

FLOCKCARE: DEVELOPMENT OF A WEB-BASED GAMEFOWL
MANAGEMENT AND MONITORING SYSTEM
BSIT Capstone Project Concept Paper

INTRODUCTION
Background of the Project
Gamefowl breeding and farm management require consistent monitoring of flock bloodlines, health regimens, breeding cycles, and medical inventory. However, many local gamefowl farms and backyard breeders still rely on manual logbooks, handwritten notebooks, and scattered spreadsheets to record bird profiles, vaccination dates, breeding pairings, medicine stock levels, and operating expenses. This traditional record-keeping approach frequently results in missed vaccination or deworming boosters, expired or depleted medical supplies, inaccurate win-loss and lineage tracking, untracked farm costs, and disorganized preparation prior to derby events.
To address these operational challenges, the proposed project will focus on developing FlockCare, a centralized, web-based Gamefowl Management and Monitoring System. The web application will digitize flock profiling, automate health and vaccination reminder alerts, track breeding records and fight/weight history, monitor medicine cabinet inventory with expiration notifications, and record per-flock-member expenses, providing an organized, reliable, and data-driven management platform for breeders and farm caretakers.

Statement of the Problem or Project Objectives
The main objective of this project is to design, develop, and evaluate FlockCare, a web-based Gamefowl Management and Monitoring System, to streamline flock record-keeping, health scheduling, breeding management, medical inventory management, and expense tracking.
Specifically, the project aims to accomplish the following technical objectives:

-Develop a centralized flock profiling module that records individual bird identifiers (wingband or legband tags), bloodline breeds, gender classifications (Stag, Cock, Broodcock, Broodhen, Pullet, Hen), status categories (Active, Broodcock, Broodhen, Retired, Sold), and win-loss-draw performance records.
-Implement a health care scheduling and automated reminder module that logs vaccinations, deworming, vitamins, and treatments while flagging overdue and upcoming due-within-30-days follow-ups.
-Integrate a breeding management module to monitor pairings, clutch and hatch records, and lineage across the flock, together with per-bird weight and fight-history logs.
-Develop a medicine cabinet inventory module with category filtering, stock level alerts (Low Stock, Out of Stock), expiration tracking (Expiring in 30 Days, Expired), and per-unit cost so the total cabinet value is visible.
- Build an analytics dashboard summarizing total flock population, active birds, win-loss-draw records, overdue health alerts, and monthly/all-time expense totals, and conduct user acceptance testing (UAT) with breeders and farm handlers to evaluate usability and system performance.
- Develop an expense tracking module that records feed, medicine, equipment, transport, entry fees, labor, utilities, and other costs per flock member, with monthly and all-time summaries.

Significance of the Project
Alignment with Institutional Research Agenda and Sustainable Development Goals
- Institutional Research Agenda Alignment: Aligns with the Institutional Information Technology and Agricultural Modernization Research priority by leveraging web-based software solutions to digitize livestock management and improve farm productivity.

The proposed system will provide direct practical value to the following beneficiaries:

- Gamefowl Breeders and Farm Owners: Centralizes bloodline records, competitive win-loss analytics, breeding lineages, and per-bird expense history, enabling informed selection and strategic farm management.
- Farm Handlers and Caretakers: Eliminates missed vaccinations, deworming schedules, and supplement administrations through automated overdue and upcoming health care alerts.
- Farm Supply and Inventory Custodians: Prevents medicine stockouts and spoilage by tracking real-time stock quantities, low-stock thresholds, and upcoming expiration dates.
- Future Researchers and IT Students: Serves as a practical reference framework for developing Django-based agricultural and livestock management information systems.

- Sustainable Development Goal Alignment:
o SDG 9 (Industry, Innovation, and Infrastructure): Fosters technological innovation in local agricultural and livestock operations through accessible digital record-keeping and automated monitoring tools.
o SDG 12 (Responsible Consumption and Production): Promotes efficient inventory management of veterinary medicines and supplements, minimizing waste from expired supplies and supporting responsible animal health care.

SCOPE AND LIMITATIONS
System Scope & Technical Architecture
Component	Description & Coverage
Core Modules	Executive Summary Dashboard, Flock Profiling & Bloodline Management, Breeding Records, Health Care & Vaccination Schedule with Overdue Alerts, Medicine Cabinet Inventory Management, Fight & Weight Logging, and Per-Flock-Member Expense Tracking.
Technology Stack	Web-based architecture utilizing Python and the Django Web Framework for backend processing, SQLite/MySQL for relational database management, and HTML5, CSS3, and JavaScript for a responsive dark-themed user interface.
Target Users	Gamefowl Breeders, Farm Owners, Farm Caretakers, and Farm Supply and Inventory Custodians managing flock health, breeding, and veterinary supplies.

Limitations
- The system will operate as a local server or web-hosted application tailored for individual or single-farm gamefowl management and does not support multi-farm marketplace transactions.

- SMS gateway notifications, mobile push notifications, automated RFID/barcode hardware scanning, income and sales tracking, payroll, tax reporting, and full financial accounting are excluded from the current development phase and may be recommended for future enhancements. The system records operating expenses only.



Member:
Mark Aldrin Millan
Brent Justine Maigue
Gino Polohimon

