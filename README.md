# Hatef Life RPG OS - Rebuild Era

A maintainable Django template-based Life RPG dashboard. It uses SQLite for local development, Django auth, CSRF-protected POST actions, Django timezone utilities, persistent weekly content, and a merchant-style reward shop.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_defaults
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## First User

Use the Signup page to create a local user. The app automatically creates a player profile and the current weekly run for each authenticated user.

## Useful Commands

```bash
python manage.py createsuperuser
python manage.py seed_defaults
python manage.py simulate_week_rollover hatef --date 2026-05-11
python manage.py test
```

## Structure

- `config/` - Django project settings and root URLs.
- `core/models.py` - Profile, fixed quests, quick actions, shop, weekly templates/instances, gift fund, smoking, journal, weekly stats, and reward ledger.
- `core/services.py` - XP/coins, level curve, weekly rollover, random weekly generation, shop purchases, bonuses, boss damage, milestones, and archives.
- `core/middleware.py` - Authenticated request hook that creates or rolls over weekly runs.
- `core/views.py` - Function-based views with POST actions.
- `templates/` - Django templates and reusable partials.
- `static/core/` - Custom CSS and small vanilla JS.

## Pages

- Dashboard
- Daily Quests
- Quick Actions
- Boss Arena
- Weekly Content
- Gift Fund
- Shop
- Smoking Tracker
- Journal / Mental Check-in
- Weekly Review
- Admin Panel

## Mechanics

- Fixed daily core quests are always present and are seeded by `seed_defaults`.
- Daily quest completion grants XP and coins once per quest per date.
- Uncompleting a quest reverses that quest reward, so repeated toggles cannot farm XP.
- Combo bonus unlocks after 3 completed daily quests and can be claimed once per day.
- Perfect Day unlocks when all active daily quests are complete and can be claimed once per day.
- Weekly runs start on Monday and end on Sunday.
- On authenticated requests, the app checks the active `WeeklyRun`; if a new week started, it archives the old run into `WeeklyStats`, marks it inactive, and creates one new boss, two challenges, and one random event.
- Weekly content is stored in database instances and does not reroll on refresh.
- Gift milestones unlock every 5M تومان and award XP, coins, badges, and optional titles once per user.
- Shop rewards spend coins. Non-repeatable items cannot be bought twice.
- Visible dates use English-readable formatting, for example `Saturday, May 9, 2026`.
