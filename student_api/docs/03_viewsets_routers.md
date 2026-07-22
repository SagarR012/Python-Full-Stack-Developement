# Lesson 3 — ViewSets & Routers

## What is a ViewSet?

A ViewSet is a class that groups related views together. Instead of writing
separate view functions for list, create, retrieve, update, delete — you write
one ViewSet and get all of them.

```
One ViewSet → 6 URL patterns (automatically)
```

---

## ModelViewSet — Full CRUD in One Class

```python
# apps/students/views.py

class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet gives you these actions automatically:
      list          → GET  /students/
      create        → POST /students/
      retrieve      → GET  /students/{id}/
      update        → PUT  /students/{id}/
      partial_update→ PATCH /students/{id}/
      destroy       → DELETE /students/{id}/
    """

    filterset_class = StudentProfileFilter
    search_fields = ['student_id', 'user__username', 'user__first_name']
    ordering_fields = ['student_id', 'enrollment_date']
    ordering = ['student_id']

    def get_queryset(self):
        # Controls WHAT data is returned
        return StudentProfile.objects.select_related('user', 'department').all()

    def get_serializer_class(self):
        # Controls HOW data is serialized — different per action
        if self.action == 'list':
            return StudentProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StudentProfileCreateUpdateSerializer
        return StudentProfileDetailSerializer   # retrieve + default

    def get_permissions(self):
        # Controls WHO can access — different per action
        if self.action in ['list', 'retrieve', 'my_profile']:
            return [IsAuthenticated()]
        return [IsTeacherOrAdmin()]
```

### self.action — What is the Current Action?

Inside a ViewSet, `self.action` tells you which HTTP method is being handled:

| self.action     | HTTP Method       | URL               |
|----------------|-------------------|-------------------|
| `list`         | GET               | `/students/`      |
| `create`       | POST              | `/students/`      |
| `retrieve`     | GET               | `/students/{id}/` |
| `update`       | PUT               | `/students/{id}/` |
| `partial_update` | PATCH           | `/students/{id}/` |
| `destroy`      | DELETE            | `/students/{id}/` |
| custom action name | any           | custom URL        |

---

## select_related — Query Optimization

Without `select_related`, accessing `student.user.username` for 100 students
makes **101 queries** (1 for students + 100 for users). This is the N+1 problem.

```python
# BAD — N+1 queries
def get_queryset(self):
    return StudentProfile.objects.all()
    # For each student, Django makes a separate query for .user and .department

# GOOD — 1 query with SQL JOINs
def get_queryset(self):
    return StudentProfile.objects.select_related('user', 'department').all()
    # Django JOINs the tables: SELECT * FROM students JOIN users JOIN departments
```

Use `select_related` for ForeignKey and OneToOneField.
Use `prefetch_related` for ManyToManyField.

---

## Custom Actions — @action

Standard CRUD is not always enough. Use `@action` for extra endpoints.

### detail=True — Acts on a Single Object

```python
# apps/courses/views.py

@action(detail=True, methods=['post'], url_path='drop',
        permission_classes=[IsAuthenticated])
def drop_course(self, request, pk=None):
    """
    POST /api/v1/enrollments/{id}/drop/

    detail=True → {id} is required in the URL
    url_path='drop' → the URL segment after {id}/
    """
    enrollment = self.get_object()  # Gets enrollment by pk, checks permissions

    if enrollment.status == Enrollment.Status.DROPPED:
        return Response(
            {'error': 'Already dropped.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    enrollment.drop_course()  # Business logic lives in the model
    return Response(
        EnrollmentDetailSerializer(enrollment).data,
        status=status.HTTP_200_OK
    )
```

### detail=False — Acts on the Collection

```python
@action(detail=False, methods=['get'], url_path='my-enrollments',
        permission_classes=[IsAuthenticated])
def my_enrollments(self, request):
    """
    GET /api/v1/enrollments/my-enrollments/

    detail=False → no {id} in the URL
    Returns data scoped to the current user
    """
    try:
        student_profile = request.user.student_profile
    except Exception:
        return Response({'error': 'No student profile found.'}, status=404)

    enrollments = Enrollment.objects.filter(student=student_profile)

    # Apply pagination — same as the standard list action
    page = self.paginate_queryset(enrollments)
    if page is not None:
        serializer = EnrollmentListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = EnrollmentListSerializer(enrollments, many=True)
    return Response(serializer.data)
```

---

## Routers — Automatic URL Generation

```python
# apps/students/urls.py

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'students', views.StudentProfileViewSet, basename='student')
router.register(r'teachers', views.TeacherProfileViewSet, basename='teacher')

urlpatterns = [
    path('', include(router.urls)),
]
```

One `router.register()` call generates all these URLs:

```
GET    /api/v1/students/               list
POST   /api/v1/students/               create
GET    /api/v1/students/{id}/          retrieve
PUT    /api/v1/students/{id}/          update
PATCH  /api/v1/students/{id}/          partial_update
DELETE /api/v1/students/{id}/          destroy
GET    /api/v1/students/my-profile/    my_profile  (@action detail=False)
```

---

## Data Scoping in get_queryset()

Different users should see different data. Put this logic in `get_queryset()`:

```python
# apps/grades/views.py

def get_queryset(self):
    user = self.request.user

    if user.is_admin:
        return Grade.objects.select_related('student__user', 'course').all()

    if user.is_teacher:
        # Teachers only see grades for their courses
        return Grade.objects.filter(course__teacher=user)

    # Students only see their own grades
    try:
        return Grade.objects.filter(student=user.student_profile)
    except Exception:
        return Grade.objects.none()  # Return empty queryset, not an error
```

This means `GET /api/v1/grades/` returns:
- All grades for admins
- Course-specific grades for teachers
- Personal grades for students

The same URL, different results based on who's asking.

---

## Disabling HTTP Methods

Sometimes you don't want all CRUD operations:

```python
# apps/courses/views.py — EnrollmentViewSet

# Disable PUT and PATCH — use custom drop_course action instead
http_method_names = ['get', 'post', 'delete', 'head', 'options']
```

---

## ViewSet vs Generic Views

This project uses both:

```python
# ModelViewSet — when you need full CRUD
class StudentProfileViewSet(viewsets.ModelViewSet):
    ...

# Generic views — when you need just one or two actions
class UserRegistrationView(generics.CreateAPIView):
    # Only POST, no GET/PUT/DELETE
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    # Only GET, PUT, PATCH
    def get_object(self):
        return self.request.user  # Always returns the current user
```

---

## Try It

In Swagger (http://127.0.0.1:8000/api/docs/):

1. Authenticate: POST `/api/v1/auth/login/` with your credentials
2. Click "Authorize" and paste the access token
3. Try GET `/api/v1/courses/` — notice it works without auth (public)
4. Try GET `/api/v1/students/` — requires auth
5. Try GET `/api/v1/grades/` — returns only your own grades (scoped!)

---

## Key Takeaways

1. `ModelViewSet` gives you CRUD for free — customize with `get_queryset()`,
   `get_serializer_class()`, and `get_permissions()`
2. `self.action` tells you which action is currently running
3. `select_related()` prevents N+1 queries — always use it for FKs
4. `@action(detail=True)` for operations on a single object (like "drop course")
5. `@action(detail=False)` for operations on the collection (like "my courses")
6. `DefaultRouter` auto-generates all URL patterns from one `register()` call
7. `get_queryset()` is where you scope data per user role
