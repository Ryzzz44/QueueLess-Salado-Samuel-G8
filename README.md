# QueueLess

QueueLess is a virtual queue-management web app for school services (document requests, payments, and other transactions). Students join a queue online, get a queue number, and track their position instead of waiting in a physical line. Staff manage services and move the queue along.

**Proponent:** Salado, Samuel O. · IT317

## Tech Stack

- Full-stack Django (Django templates + Bootstrap 5)
- PostgreSQL via Supabase
- Django built-in authentication (hashed passwords)

## Core Feature (Project Development 2): Virtual Queue

A full vertical slice: models and migrations in PostgreSQL/Supabase, Django views/forms/URLs, and templates.

### Student

- **Join a queue:** pick an open service, enter a purpose, and get a number such as `REG-001`
- **Track the queue:** see your position, how many are ahead, and the number now being served (auto-refreshes)
- **Edit** the purpose of a waiting ticket, or **cancel** it
- **My Tickets:** active tickets and history; **remove** finished tickets from your history

### Staff

- **Manage services:** create, edit, delete, and open/close services (e.g. Registrar, Cashier)
- **Queue board:** see who is waiting, **Call Next**, then **Complete** or **Skip**
- **Dashboard:** waiting and served counts for today, and the status of each queue

### Business rules and validation

- Required fields, purpose of at least 5 characters, service code of 2–5 capital letters, unique service name and code
- Students can only join **open** services and can hold only **one active ticket per service per day**
- Queue numbers are given out in order per service per day and are **never reused**, even if a ticket is deleted
- Only one ticket can be "Now Serving" per service; staff must complete or skip it before calling the next
- Only **waiting** tickets can be edited or cancelled; only **finished** tickets can be removed
- A service with queue records cannot be deleted; it can be closed instead

### Access control

- All pages require login; logged-out users are sent to the login page
- Student-only and staff-only pages are blocked for the other role
- Students can only view and change **their own** tickets (others return 404); staff can view all tickets

### Data model

| Model             | Key fields                                                   | Relationships                                             |
| ----------------- | ------------------------------------------------------------ | --------------------------------------------------------- |
| `User` (accounts) | username, email, role (Student/Staff), contact number, photo | —                                                         |
| `Service`         | name, code, office, description, is_open                     | `created_by` → User                                       |
| `QueueTicket`     | number, queue_date, purpose, status, timestamps              | `student` → User, `service` → Service, `served_by` → User |

## Standard Features (Project Development 1)

- Registration with validation and hashed passwords
- Login / logout with protected pages
- Role-based dashboards (Student and Staff)
- User profile view and edit

Public registration creates **Student** accounts. **Staff** accounts are created by an administrator in the Django admin (`/admin/`) by setting Role = Staff.

## Setup

Requires **Python 3.12 or newer**.

```bash
git clone https://github.com/Ryzzz44/QueueLess-Salado-Samuel-G8.git
cd QueueLess-Salado-Samuel-G8
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your own values (Supabase **Session pooler** connection string), then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py shell -c "from accounts.models import User; User.objects.filter(username='admin').update(role='STAFF')"
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Branching

- `main`: stable code only
- `develop`: integration branch
- `feature/service-management`, `feature/virtual-queue`: feature branches merged into `develop` through pull requests
