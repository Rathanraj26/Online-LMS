# RR - Online Learning Management System

A full-stack LMS with a Flask + MySQL REST API backend and an HTML/CSS/Bootstrap 5/vanilla-JS frontend, supporting three roles — **Student**, **Instructor**, and **Admin**.

---

## 1. Project Structure

```
Online-LMS/
├── frontend/
│   ├── index.html, login.html, register.html, dashboard.html,
│   │   courses.html, course-details.html, learning.html,
│   │   assignments.html, quiz.html, results.html,
│   │   certificate.html, profile.html
│   ├── css/  (style.css, login.css, dashboard.css, courses.css, quiz.css, responsive.css)
│   └── js/   (app.js, auth.js, courses.js, assignments.js, quiz.js, profile.js, api.js)
│
└── backend/
    ├── app.py, config.py, requirements.txt, .env
    ├── database/   (database.py, schema.sql)
    ├── routes/     (auth, users, courses, enrollment, assignments, quiz, progress, certificate)
    ├── models/     (user_model, course_model, assignment_model, quiz_model)
    ├── middleware/ (auth_middleware, role_middleware)
    ├── utils/      (helper, validator, response)
    └── uploads/    (profile/, courses/, assignments/)
```

---

## 2. Prerequisites

- Python 3.10+
- MySQL 8.0+
- A modern browser (frontend needs no build step)

---

## 3. Backend Setup

```bash
cd Online-LMS/backend

# 1. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
# Edit .env and set your real MySQL password + secret keys:
#   DB_PASSWORD=your_mysql_password
#   SECRET_KEY=<generate a random string>
#   JWT_SECRET_KEY=<generate a random string>

# 4. Create the database schema
mysql -u root -p < database/schema.sql

# 5. Run the API server
python app.py
```

The API will start on **http://localhost:5000**. Verify it's running:

```bash
curl http://localhost:5000/api/health
```

### Creating the first Admin account

Public registration only allows `student` / `instructor` roles (by design — admins are provisioned directly). After registering a normal account, promote it to admin manually:

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

---

## 4. Frontend Setup

The frontend is static HTML/CSS/JS — no build tooling required. Serve it with any static file server, for example:

```bash
cd Online-LMS/frontend
python3 -m http.server 5500
```

Then open **http://localhost:5500/index.html** in your browser.

> The frontend calls the API at `http://localhost:5000/api` (see `js/api.js` → `API_BASE_URL`). Update that constant if your backend runs on a different host/port.

---

## 5. Default User Flows

| Role | What they can do |
|---|---|
| **Student** | Register/login, browse & enroll in courses, watch lessons, download notes, submit assignments, take timed quizzes, view results, track progress, download certificates on 100% completion |
| **Instructor** | Create courses, upload video/PDF lessons, create assignments & quizzes, grade submissions, view enrolled students |
| **Admin** | View/disable/delete users, view all courses, basic system overview |

---

## 6. Security Notes

- Passwords are hashed with **bcrypt** before storage — never stored in plain text.
- Authentication uses **JWT** (`Authorization: Bearer <token>`), expiring after `JWT_EXP_HOURS` (default 24h).
- All SQL queries use **parameterized statements** (`%s` placeholders) to prevent SQL injection.
- Role-based route protection via `@token_required` + `@role_required(...)` decorators.
- File uploads are restricted by extension whitelist and renamed to random UUIDs on save.
- Update `SECRET_KEY` / `JWT_SECRET_KEY` in `.env` before any real deployment — the shipped defaults are for local development only.

---

## 7. API Reference (summary)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/register | — | Create account |
| POST | /api/login | — | Get JWT |
| POST | /api/logout | — | Client-side token discard |
| GET | /api/users | Admin | List users |
| GET/PUT | /api/profile | Any | View/update own profile |
| GET | /api/courses | — | List/search courses |
| POST/PUT/DELETE | /api/courses(/<id>) | Instructor/Admin | Manage courses |
| POST | /api/courses/<id>/lessons | Instructor/Admin | Upload lesson |
| POST | /api/enroll | Student | Enroll in a course |
| GET | /api/my-courses | Student | Enrolled courses |
| GET/POST | /api/assignments | Any / Instructor | List / create |
| POST | /api/submissions | Student | Submit assignment |
| PUT | /api/submissions/<id>/grade | Instructor | Grade submission |
| GET/POST | /api/quizzes | Any / Instructor | List / create |
| POST | /api/results | Student | Submit quiz answers (auto-graded) |
| GET | /api/results | Student | View own results |
| POST/GET | /api/certificate/<course_id> | Student | Generate/fetch certificate |

Full request/response contracts are documented as docstrings at the top of each file in `backend/routes/`.

---

## 8. Production Checklist

- [ ] Set strong, unique `SECRET_KEY` / `JWT_SECRET_KEY`
- [ ] Run behind a WSGI server (gunicorn/uWSGI) + reverse proxy (nginx), not `flask run`
- [ ] Restrict CORS `origins` in `app.py` to your real frontend domain
- [ ] Enable HTTPS
- [ ] Move `uploads/` to object storage (S3, etc.) for horizontal scaling
- [ ] Add DB backups / migrations tooling (e.g. Alembic) as the schema evolves
