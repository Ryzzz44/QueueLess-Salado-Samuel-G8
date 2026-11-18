# QueueLess

QueueLess is a virtual queue-management web app for school services (document requests, payments, and other transactions). Students can join a queue and track their position instead of waiting in a physical line, and staff can manage the queue.

**Proponent:** Salado, Samuel O. · IT317

## Tech Stack
- Full-stack Django (Django templates + Bootstrap 5)
- PostgreSQL via Supabase
- Django built-in authentication (hashed passwords)

## Project Development 1: Account Feature
- **Registration:** required fields, valid email, unique username and email, password confirmation, password hashing, success and error messages
- **Login / Logout:** invalid-credential error message; logout ends the session
- **Protected pages:** `@login_required` sends logged-out users to the login page
- **Role-based dashboards:** Student and Staff; each user is redirected to their own dashboard and blocked from the other role's dashboard
- **User profile:** view and edit your own name, email, contact number, and profile photo

Public registration creates **Student** accounts. **Staff** accounts are created by an administrator in the Django admin (`/admin/`) by setting Role = Staff.

## Setup
```bash
git clone https://github.com/Ryzzz44/QueueLess-Salado-Samuel-G8.git
cd QueueLess-Salado-Samuel-G8
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your own values, then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/