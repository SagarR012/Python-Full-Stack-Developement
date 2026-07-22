# Student Management REST API

**Practice Project** — Django REST Framework & JWT

This is the hands-on practice project that mirrors every concept
taught in the Library Management API (`../library_api`).
Work through it after studying each lesson doc in `library_api/docs/`.

---

## Learning Objectives

By building this project you practice:

| Concept | Where to find it |
|---------|-----------------|
| Custom User model + roles | `apps/accounts/models.py` |
| JWT login / refresh / logout | `apps/accounts/urls.py` |
| Serializer validation | `apps/*/serializers.py` |
| ModelViewSet + Router | `apps/*/views.py` + `urls.py` |
| Dynamic permissions | `apps/accounts/permissions.py` |
| Custom @action endpoints | `apps/courses/views.py`, `apps/grades/views.py` |
| FilterSet (field filtering) | `apps/*/filters.py` |
| SearchFilter + OrderingFilter | ViewSet `search_fields`, `ordering_fields` |
| Throttling + Pagination | `student_api/settings.py` |
| Swagger / ReDoc | `http://localhost:8000/api/docs/` |
| Postman collection | `postman/Student_API.postman_collection.json` |

---

## Compare Every File with the Library API

| Student API | Library API | Concept |
|-------------|-------------|---------|
| `accounts/models.py` → Role: Admin/Teacher/Student | `accounts/models.py` → Role: Admin/Librarian/Member | Custom User + TextChoices |
| `accounts/permissions.py` → IsTeacherOrAdmin | `accounts/permissions.py` → IsLibrarianOrAdmin | Custom permission |
| `students/models.py` → Department + StudentProfile | `books/models.py` → Category + Book | ForeignKey, SlugField |
| `courses/models.py` → Enrollment | `loans/models.py` → Loan | Junction table, TextChoices |
| `grades/models.py` → Grade.save() auto-computes letter | `books/models.py` → Book.borrow() | Model business logic |
| `courses/views.py` → drop_course @action | `loans/views.py` → return_book @action | detail=True custom action |
| `courses/views.py` → my_enrollments @action | `loans/views.py` → my_loans @action | detail=False custom action |
| `grades/views.py` → transcript @action | — | Non-model response |

---

## Project Structure

```
student_api/
├── manage.py
├── requirements.txt
├── .env.example
├── student_api/          ← Project config
│   ├── settings.py       ← DRF, JWT, Spectacular config
│   └── urls.py           ← Root URL dispatcher
├── apps/
│   ├── accounts/         ← User model, JWT auth, permissions
│   ├── students/         ← Department, StudentProfile, TeacherProfile
│   ├── courses/          ← Course, Enrollment
│   └── grades/           ← Grade records, transcript
└── postman/
    └── Student_API.postman_collection.json
```

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
copy .env.example .env         # Windows
cp .env.example .env           # macOS/Linux

# 4. Run migrations
python manage.py migrate

# 5. Create a superuser (admin)
python manage.py createsuperuser

# 6. Set the admin role via shell
python manage.py shell
>>> from apps.accounts.models import User
>>> u = User.objects.get(username='your_superuser_name')
>>> u.role = 'admin'
>>> u.save()
>>> exit()

# 7. Start the server
python manage.py runserver
```

Visit:
- `http://localhost:8000/api/docs/` — Swagger UI
- `http://localhost:8000/api/redoc/` — ReDoc
- `http://localhost:8000/admin/` — Django Admin

---

## All API Endpoints

### Authentication (`/api/v1/auth/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register/` | Register new user | No |
| POST | `/auth/login/` | Get JWT tokens | No |
| POST | `/auth/refresh/` | Refresh access token | No |
| POST | `/auth/logout/` | Blacklist refresh token | Yes |
| GET | `/auth/profile/` | View own profile | Yes |
| PUT/PATCH | `/auth/profile/` | Update own profile | Yes |
| POST | `/auth/change-password/` | Change password | Yes |
| GET | `/auth/users/` | List all users | Admin only |

### Departments (`/api/v1/departments/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/departments/` | List departments | No |
| POST | `/departments/` | Create department | Teacher/Admin |
| GET | `/departments/{id}/` | Department detail | No |
| PUT/PATCH | `/departments/{id}/` | Update department | Teacher/Admin |
| DELETE | `/departments/{id}/` | Delete department | Teacher/Admin |

### Students (`/api/v1/students/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/students/` | List students | Authenticated |
| POST | `/students/` | Create student profile | Teacher/Admin |
| GET | `/students/{id}/` | Student detail | Authenticated |
| PUT/PATCH | `/students/{id}/` | Update student | Teacher/Admin |
| DELETE | `/students/{id}/` | Delete student | Teacher/Admin |
| GET | `/students/my-profile/` | Own student profile | Authenticated |

### Teachers (`/api/v1/teachers/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/teachers/` | List teachers | Authenticated |
| POST | `/teachers/` | Create teacher profile | Admin only |
| GET | `/teachers/{id}/` | Teacher detail | Authenticated |
| PUT/PATCH | `/teachers/{id}/` | Update teacher | Admin only |
| DELETE | `/teachers/{id}/` | Delete teacher | Admin only |

### Courses (`/api/v1/courses/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/courses/` | List courses | No |
| POST | `/courses/` | Create course | Teacher/Admin |
| GET | `/courses/{id}/` | Course detail | No |
| PUT/PATCH | `/courses/{id}/` | Update course | Teacher/Admin |
| DELETE | `/courses/{id}/` | Delete course | Admin only |
| GET | `/courses/my-courses/` | Courses I'm in/teaching | Authenticated |

### Enrollments (`/api/v1/enrollments/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/enrollments/` | List enrollments (scoped) | Authenticated |
| POST | `/enrollments/` | Enroll student | Teacher/Admin |
| GET | `/enrollments/{id}/` | Enrollment detail | Authenticated |
| DELETE | `/enrollments/{id}/` | Cancel enrollment | Admin only |
| POST | `/enrollments/{id}/drop/` | Drop course | Student (own) / Teacher/Admin |
| GET | `/enrollments/my-enrollments/` | Own enrollments | Authenticated |

### Grades (`/api/v1/grades/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/grades/` | List grades (scoped) | Authenticated |
| POST | `/grades/` | Enter a grade | Teacher/Admin |
| GET | `/grades/{id}/` | Grade detail | Authenticated |
| PUT/PATCH | `/grades/{id}/` | Update grade | Teacher/Admin |
| DELETE | `/grades/{id}/` | Delete grade | Admin only |
| GET | `/grades/my-grades/` | Own grades | Authenticated |
| GET | `/grades/transcript/` | Full transcript + GPA | Authenticated |

---

## Key Filtering Options

```
# Students
GET /api/v1/students/?department=1
GET /api/v1/students/?year_level=2
GET /api/v1/students/?active=true
GET /api/v1/students/?status=graduated
GET /api/v1/students/?search=alice
GET /api/v1/students/?ordering=-enrollment_date

# Courses
GET /api/v1/courses/?available=true
GET /api/v1/courses/?department_slug=computer-science
GET /api/v1/courses/?credits=3
GET /api/v1/courses/?search=programming
GET /api/v1/courses/?ordering=course_code

# Enrollments
GET /api/v1/enrollments/?status=enrolled
GET /api/v1/enrollments/?course_code=CS101
GET /api/v1/enrollments/?student_id=STU-2024-001

# Grades
GET /api/v1/grades/?course_code=CS101
GET /api/v1/grades/?min_score=80&max_score=100
GET /api/v1/grades/?letter_grade=A
GET /api/v1/grades/?student_id=STU-2024-001
```

---

## JWT Flow (same as Library API)

```
# 1. Login
POST /api/v1/auth/login/
Body: {"username": "alice", "password": "pass123"}
Response: {"access": "eyJ...", "refresh": "eyJ..."}

# 2. Use API with access token
GET /api/v1/students/
Header: Authorization: Bearer eyJ...access...

# 3. Refresh (access token expires after 15 min)
POST /api/v1/auth/refresh/
Body: {"refresh": "eyJ...old_refresh..."}
Response: {"access": "eyJ...new...", "refresh": "eyJ...new_refresh..."}

# 4. Logout
POST /api/v1/auth/logout/
Body: {"refresh": "eyJ...refresh..."}
```

---

## Role Permissions Summary

| Action | Student | Teacher | Admin |
|--------|---------|---------|-------|
| Read departments/courses | ✅ | ✅ | ✅ |
| Create/edit courses | ❌ | ✅ | ✅ |
| Enroll students | ❌ | ✅ | ✅ |
| Enter grades | ❌ | ✅ | ✅ |
| See own data only | ✅ | — | — |
| See all data | ❌ | Partial | ✅ |
| Manage users/teachers | ❌ | ❌ | ✅ |
| Delete anything | ❌ | ❌ | ✅ |

---

## Student Exercises

These are listed throughout the code as `# STUDENT EXERCISE:` comments.

**Beginner**
1. Add a `validate_phone_number` method to `UserRegistrationSerializer`
2. Add a `student_count` property to `Department` model
3. Add a `?semester=` filter to `CourseFilter`

**Intermediate**
4. Add a `GET /api/v1/departments/{id}/students/` custom action
5. Add a `GET /api/v1/courses/{id}/students/` endpoint (teacher/admin only)
6. Add a `POST /api/v1/enrollments/{id}/complete/` action
7. Implement a `GPA` property on `StudentProfile` that calculates from grades

**Advanced**
8. Add a `GET /api/v1/grades/course-summary/` endpoint that returns
   `{course, average_score, highest, lowest, grade_distribution}`
9. Implement custom JWT claims (add `role` and `full_name` to token payload)
10. Add throttling: limit grade entry to 100/hour for teachers
11. Add an admin-only `?student_id=` override to the transcript endpoint

---

## Postman Setup

1. Import `postman/Student_API.postman_collection.json`
2. Create an environment `Student API - Local` with:
   - `base_url` = `http://localhost:8000`
   - `access_token` = *(empty)*
   - `refresh_token` = *(empty)*
3. Run **Login (saves tokens)** first
4. All other requests will work automatically using `{{access_token}}`

The collection includes automated tests on every request.
Use **Collection Runner** to run the full suite at once.
