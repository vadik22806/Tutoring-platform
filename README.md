# EchoServer

## Overview
EchoServer is a Django tutoring platform with a custom MongoDB-backed data model and user flows for students, tutors, and administrators.

The app supports:
- login by email or phone
- student and tutor registration
- role-based dashboards
- lesson creation, booking, editing, cancellation, and completion
- saved lessons (cart-like workflow)
- booking history
- profile editing
- a custom `User` model with `djongo` / MongoDB storage

## Project Structure
```
echoserver/
├── manage.py                     # Django command-line utility
├── echoserver/                   # Project configuration package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py               # Project settings, MongoDB / djongo configuration
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py
├── main/                         # Core application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── authentication.py         # Email/phone authentication backend
│   ├── forms.py
│   ├── models.py                 # Custom user model, subjects, lessons, saved lessons
│   ├── mongo_db.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   ├── static/main/              # Static assets (CSS, images, JS)
│   └── templates/main/           # HTML templates
├── db.sqlite3                    # Local database file (leftover from development)
└── README.md                     # Project documentation
```

## Requirements
The current project uses:
- Python 3.10+ (recommended)
- Django 6.0.2
- djongo
- pymongo
- dnspython
- MongoDB running locally on `mongodb://localhost:27017`

> Note: `settings.py` is configured for MongoDB/djongo. The included `db.sqlite3` appears to be a development artifact and is not used by the current database settings.

## Setup & Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd echoserver
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install Django==6.0.2 djongo pymongo dnspython
   ```
4. Start or verify your MongoDB server:
   - Default host: `mongodb://localhost:27017`
   - Default database name: `Tutoring`
   - Database settings are in `echoserver/settings.py`
5. Apply Django migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`.

## Running Tests
Run the Django unit tests:
```bash
python manage.py test
```

Run Selenium / end-to-end tests:
```bash
python -m unittest discover -s test
```

## Useful Links
- Admin dashboard: `http://127.0.0.1:8000/admin/`
- Student dashboard: `http://127.0.0.1:8000/dashboard/student/`
- Tutor dashboard: `http://127.0.0.1:8000/dashboard/tutor/`

## Contributing
Contributions are welcome. Fork the repository, create a feature branch, and submit a pull request.
Please ensure code style is consistent and tests pass before submitting changes.

## License
This project is licensed under the MIT License – see the `LICENSE` file for details.
