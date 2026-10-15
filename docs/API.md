# API & Interface Reference

Welcome to the **Digital Course & Asset Marketplace API** reference documentation. This specification covers all endpoints, authentication schemas, query parameters, permissions, request/response bodies, and HTTP status codes.

---

## Table of Contents
1. [Global Conventions & Headers](#global-conventions--headers)
2. [Authentication & Accounts](#1-authentication--accounts)
   - [Register Student](#post-apicreateuser)
   - [Register Instructor](#post-apicreateinstructor)
   - [Login (Obtain JWT Pair)](#post-apiregister)
   - [Refresh Access Token](#post-apitokenrefresh)
3. [Courses & Digital Assets](#2-courses--digital-assets)
   - [List Courses (Paginated, Filtered, Cached)](#get-apigetcourses)
   - [Get Course Detail](#get-apigetcoursecourse_id)
   - [Create Course (Instructor Only)](#post-apicreatecourse)
4. [Orders & Checkout](#3-orders--checkout)
   - [Create Order / Purchase Asset](#post-apicreateorder)
   - [List Student Orders](#get-apiorders)
   - [Get Order Detail](#get-apiorderorder_id)
5. [Analytics & Financial Reporting](#4-analytics--financial-reporting)
   - [Instructor Revenue Report](#get-apigetrevenue)
6. [System Discovery & Diagnostics](#5-system-discovery--diagnostics)
   - [API Root Discovery](#get-api)
   - [Silk Profiler Dashboard](#get-silk)
7. [Standard Error Codes & Responses](#standard-error-codes--responses)

---

## Global Conventions & Headers

### Base URL
```text
http://127.0.0.1:8000
```

### Authentication Header
Endpoints requiring authentication must include the `Authorization` header with a valid access token:
```http
Authorization: Bearer <access_token>
```

### Content Types
- Default: `Content-Type: application/json`
- Asset file/banner upload: `Content-Type: multipart/form-data`

### Pagination Format
Endpoints returning lists follow DRF `PageNumberPagination`:
```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/getcourses/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## 1. Authentication & Accounts

### `POST /api/createUser`
Registers a new platform user with the **`STUDENT`** role and automatically instantiates a 1-to-1 `Profile`.

- **Access Level**: Public (No Auth required)
- **Request Body**: `application/json`

```json
{
  "username": "student_jane",
  "email": "jane@example.com",
  "password": "StrongPassword123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "bio": "Lifelong learner and Python developer."
}
```

- **Validation Rules**:
  - `username`: Required, unique.
  - `email`: Required, valid email format.
  - `password`: Must pass Django's standard password validators.
  - `bio`: Optional text.
  - `avatar`: Optional image file (if using `multipart/form-data`).

- **Response `201 Created`**:
```json
{
  "id": 1,
  "username": "student_jane",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "STUDENT",
  "bio": "Lifelong learner and Python developer.",
  "avatar": null
}
```

- **Error Responses**:
  - `400 Bad Request`: Field validation error (e.g., username taken, weak password).

---

### `POST /api/createInstructor`
Registers a new platform user with the **`INSTRUCTOR`** role and automatically instantiates a 1-to-1 `Profile`.

- **Access Level**: Public (No Auth required)
- **Request Body**: `application/json`

```json
{
  "username": "instructor_alice",
  "email": "alice@example.com",
  "password": "StrongInstructorP@ss123!",
  "first_name": "Alice",
  "last_name": "Vance",
  "bio": "Senior Cloud Architect specializing in distributed systems."
}
```

- **Response `201 Created`**:
```json
{
  "id": 2,
  "username": "instructor_alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Vance",
  "role": "INSTRUCTOR",
  "bio": "Senior Cloud Architect specializing in distributed systems.",
  "avatar": null
}
```

---

### `POST /api/register`
Exchanges user credentials (`username` and `password`) for an HMAC-SHA256 signed JWT token pair (`access` and `refresh`).

- **Access Level**: Public (No Auth required)
- **Request Body**: `application/json`

```json
{
  "username": "instructor_alice",
  "password": "StrongInstructorP@ss123!"
}
```

- **Response `200 OK`**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwicm9sZSI6IklOU1RSVUNUT1IiLCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzYwNTAwMDAwLCJleHAiOjE3NjA1ODY0MDAsImp0aSI6ImE0ZWY3YjI3...\"...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwicm9sZSI6IklOU1RSVUNUT1IiLCJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImlhdCI6MTc2MDUwMDAwMCwiZXhwIjoxNzYxMTA0ODAwLCJqdGkiOiJkMmZhOGMy...\"..."
}
```

- **Token Claims**:
  - `sub`: User ID (string).
  - `role`: Role string (`STUDENT` or `INSTRUCTOR`).
  - `token_type`: `access` (valid for 24 hours) or `refresh` (valid for 7 days).
  - `jti`: Unique token UUID identifier to prevent replay.

- **Error Responses**:
  - `401 Unauthorized`:
```json
{
  "detail": "Invalid username or password."
}
```

---

### `POST /api/token/refresh`
Exchanges a valid refresh token for a newly signed access token.

- **Access Level**: Public (No Auth required)
- **Request Body**: `application/json`

```json
{
  "refresh": "<valid_refresh_token>"
}
```

- **Response `200 OK`**:
```json
{
  "access": "<newly_issued_access_token>"
}
```

- **Error Responses**:
  - `400 Bad Request`: `{"detail": "A refresh token is required."}`
  - `401 Unauthorized`: `{"detail": "Invalid or expired refresh token."}`

---

## 2. Courses & Digital Assets

### `GET /api/getcourses/`
Retrieves a paginated list of courses/digital assets. 
- **Role Scoping**:
  - **`STUDENT`**: Sees only assets matching `.published()` (`status=PUBLISHED`).
  - **`INSTRUCTOR`**: Sees all authored assets (`instructor=request.user`), including `DRAFT` and `PUBLISHED`.
- **Caching**: Output is cached in Redis for **60 seconds**, scoped with `Vary: Authorization`.
- **Optimization**: Queries use `select_related('instructor')` to prevent N+1 query overhead.

- **Access Level**: Authenticated (`IsAuthenticated`)
- **Query Parameters**:
  | Parameter | Type | Description | Example |
  |---|---|---|---|
  | `page` | integer | Target page number (default page size: 10) | `page=2` |
  | `search` | string | Substring search on `title` | `search=Kubernetes` |
  | `ordering` | string | Order by `price`, `-price`, `created_at`, `-created_at` | `ordering=-price` |
  | `status` | string | Exact filter (`DRAFT`, `PUBLISHED`) | `status=PUBLISHED` |
  | `price` | decimal | Exact price match | `price=49.99` |
  | `instructor`| integer | Filter by instructor ID | `instructor=2` |

- **Response `200 OK`**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Mastering Celery & Distributed Microservices",
      "description": "Learn task queues, Redis brokers, rate limiting, and atomic state updates in production.",
      "price": "79.99",
      "status": "PUBLISHED",
      "file": "/media/assets/files/celery_guide.pdf",
      "banner": "/media/assets/banners/celery_banner.jpg",
      "instructor": "instructor_alice",
      "inventory": 45,
      "created_at": "2026-10-15T09:30:00Z",
      "updated_at": "2026-10-15T09:30:00Z"
    }
  ]
}
```

---

### `GET /api/getCourse/<int:course_id>/`
Fetches a single course asset by primary key. Enforces the same role visibility rules as the list view.

- **Access Level**: Authenticated (`IsAuthenticated`)
- **Path Parameters**:
  - `course_id` (integer, required): Target Course ID.

- **Response `200 OK`**:
```json
{
  "id": 1,
  "title": "Mastering Celery & Distributed Microservices",
  "description": "Learn task queues, Redis brokers, rate limiting, and atomic state updates in production.",
  "price": "79.99",
  "status": "PUBLISHED",
  "file": "/media/assets/files/celery_guide.pdf",
  "banner": "/media/assets/banners/celery_banner.jpg",
  "instructor": "instructor_alice",
  "inventory": 45,
  "created_at": "2026-10-15T09:30:00Z",
  "updated_at": "2026-10-15T09:30:00Z"
}
```

- **Error Responses**:
  - `404 Not Found`:
```json
{
  "detail": "Course not found."
}
```

---

### `POST /api/createCourse`
Creates a new course/digital asset. Automatically binds the course's `instructor` field to `request.user`.

- **Access Level**: Authenticated **Instructor Only** (`IsAuthenticated` + `IsInstructor`)
- **Supported Content Types**: `multipart/form-data`, `application/json`
- **Request Body Fields**:
  | Field | Type | Required | Description |
  |---|---|---|---|
  | `title` | string (max 200) | **Yes** | Course title |
  | `description` | string | No | Detailed description |
  | `price` | decimal | **Yes** | Must be > `0.00` |
  | `status` | string | No | `DRAFT` (default) or `PUBLISHED` |
  | `inventory` | integer | No | Available download/purchase capacity (default: 0) |
  | `file` | file | No | Digital asset payload |
  | `banner` | image file | No | Cover image. **Strictly validated: Max 2 MB**. |

- **Example JSON Request**:
```json
{
  "title": "Advanced Event-Driven Architecture",
  "description": "Building fault-tolerant systems using distributed event logs and messaging queues.",
  "price": "89.50",
  "status": "PUBLISHED",
  "inventory": 100
}
```

- **Response `201 Created`**:
```json
{
  "id": 2,
  "title": "Advanced Event-Driven Architecture",
  "description": "Building fault-tolerant systems using distributed event logs and messaging queues.",
  "price": "89.50",
  "status": "PUBLISHED",
  "file": null,
  "banner": null,
  "instructor": "instructor_alice",
  "inventory": 100,
  "created_at": "2026-10-15T10:15:00Z",
  "updated_at": "2026-10-15T10:15:00Z"
}
```

- **Validation Errors**:
  - `400 Bad Request` (Price <= 0):
```json
{
  "price": ["Price must be greater than zero."]
}
```
  - `400 Bad Request` (Image > 2MB):
```json
{
  "banner": ["Banner image must be no larger than 2 MB."]
}
```
  - `403 Forbidden` (User is a STUDENT):
```json
{
  "detail": "Instructor accounts only."
}
```

---

## 3. Orders & Checkout

### `POST /api/createOrder/`
Executes an atomic checkout transaction for a published course asset.
- **Concurrency Protection**:
  1. Opens an atomic transaction block: `with transaction.atomic():`
  2. Acquires an exclusive row-level lock via `select_for_update()` on the target `Course`.
  3. Validates that `course.status == Course.Status.PUBLISHED`.
  4. Executes an atomic inventory decrement using Django `F()` expressions:
     ```python
     Course.objects.filter(pk=course.pk, inventory__gte=quantity).update(
         inventory=F("inventory") - quantity
     )
     ```
  5. Computes total price (`course.price * quantity`).
  6. Creates the `Order` record (`status=COMPLETED`) and related `OrderItem`.
  7. Enqueues a Celery background task using `transaction.on_commit()` to dispatch an HTML confirmation email to the student's email address.

- **Access Level**: Authenticated **Student Only** (`IsAuthenticated` + `IsStudent`)
- **Request Body**: `application/json`

```json
{
  "course_id": 1,
  "quantity": 1
}
```

- **Response `201 Created`**:
```json
{
  "id": 101,
  "student": "student_jane",
  "status": "COMPLETED",
  "total_amount": "79.99",
  "created_at": "2026-10-15T10:30:15Z",
  "items": [
    {
      "course": 1,
      "course_title": "Mastering Celery & Distributed Microservices",
      "unit_price": "79.99",
      "quantity": 1
    }
  ]
}
```

- **Error Responses**:
  - `400 Bad Request`: `{"detail": "course_id and a positive integer quantity are required."}`
  - `404 Not Found`: `{"detail": "Published course not found."}`
  - `409 Conflict` (Insufficient stock):
```json
{
  "detail": "Insufficient course inventory."
}
```
  - `403 Forbidden`: `{"detail": "Student accounts only."}`

---

### `GET /api/orders/`
Retrieves all orders placed by the currently authenticated student. Uses `select_related("student")` and `prefetch_related("items__course")` to avoid N+1 queries.

- **Access Level**: Authenticated **Student Only** (`IsAuthenticated` + `IsStudent`)

- **Response `200 OK`**:
```json
[
  {
    "id": 101,
    "student": "student_jane",
    "status": "COMPLETED",
    "total_amount": "79.99",
    "created_at": "2026-10-15T10:30:15Z",
    "items": [
      {
        "course": 1,
        "course_title": "Mastering Celery & Distributed Microservices",
        "unit_price": "79.99",
        "quantity": 1
      }
    ]
  }
]
```

---

### `GET /api/order/<int:order_id>/`
Retrieves receipt details for a specific order. Enforces tenant isolation (students can only inspect their own orders).

- **Access Level**: Authenticated **Student Only** (`IsAuthenticated` + `IsStudent`)
- **Path Parameters**:
  - `order_id` (integer, required)

- **Response `200 OK`**:
```json
{
  "id": 101,
  "student": "student_jane",
  "status": "COMPLETED",
  "total_amount": "79.99",
  "created_at": "2026-10-15T10:30:15Z",
  "items": [
    {
      "course": 1,
      "course_title": "Mastering Celery & Distributed Microservices",
      "unit_price": "79.99",
      "quantity": 1
    }
  ]
}
```

- **Error Responses**:
  - `404 Not Found`: `{"detail": "Order not found."}`

---

## 4. Analytics & Financial Reporting

### `GET /api/getRevenue/`
Computes real-time gross revenue and purchase analytics across all digital assets published by the requesting instructor.
- **ORM Pipeline**:
  - Computes `revenue_expression = ExpressionWrapper(F("order_items__unit_price") * F("order_items__quantity"), output_field=DecimalField())`
  - Runs `.annotate(purchase_count=Count("order_items__order", filter=completed, distinct=True), revenue=Sum(revenue_expression, filter=completed))` on the instructor's courses.
  - Aggregates overall totals with `.aggregate(total_revenue=Sum(...), total_purchases=Count("order_id", distinct=True))`.

- **Access Level**: Authenticated **Instructor Only** (`IsAuthenticated` + `IsInstructor`)

- **Response `200 OK`**:
```json
{
  "total_revenue": "2499.70",
  "total_purchases": 35,
  "courses": [
    {
      "id": 1,
      "title": "Mastering Celery & Distributed Microservices",
      "purchase_count": 25,
      "revenue": "1999.75"
    },
    {
      "id": 2,
      "title": "Advanced Event-Driven Architecture",
      "purchase_count": 10,
      "revenue": "499.95"
    }
  ]
}
```

- **Error Responses**:
  - `403 Forbidden`: `{"detail": "Instructor accounts only."}`

---

## 5. System Discovery & Diagnostics

### `GET /api/`
API directory endpoint returning an interactive discovery map of all system routes.

- **Access Level**: Public
- **Response `200 OK`**:
```json
{
  "create_student": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/createUser"
  },
  "create_instructor": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/createInstructor"
  },
  "login_and_get_tokens": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/register"
  },
  "refresh_access_token": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/token/refresh"
  },
  "courses": {
    "method": "GET",
    "url": "http://127.0.0.1:8000/api/getcourses/"
  },
  "course_detail": {
    "method": "GET",
    "url": "http://127.0.0.1:8000/api/getCourse/{id}/"
  },
  "create_course": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/createCourse"
  },
  "orders": {
    "method": "GET",
    "url": "http://127.0.0.1:8000/api/orders"
  },
  "create_order": {
    "method": "POST",
    "url": "http://127.0.0.1:8000/api/createOrder"
  },
  "order_detail": {
    "method": "GET",
    "url": "http://127.0.0.1:8000/api/order/{id}"
  },
  "sales_revenue_report": {
    "method": "GET",
    "url": "http://127.0.0.1:8000/api/getRevenue"
  }
}
```

---

### `GET /silk/`
Interactive profiling UI provided by **Django Silk**. Profiles database queries, execution latency, and N+1 query diagnostics across all API routes.

- **Access Level**: Staff / Superuser or Development Environment.
- **URL**: `http://127.0.0.1:8000/silk/`

---

## Standard Error Codes & Responses

| Status Code | Meaning | Typical Trigger |
|---|---|---|
| `200 OK` | Request succeeded | Successful GET, login, or token refresh |
| `201 Created` | Resource instantiated | User registration, course creation, order placement |
| `400 Bad Request` | Payload validation failure | Negative price, banner file > 2MB, missing fields |
| `401 Unauthorized` | Invalid / expired credentials | Missing or malformed Bearer token, bad password |
| `403 Forbidden` | Role permission denied | Student attempting to create courses or view revenue |
| `404 Not Found` | Entity does not exist | Course or order ID not found, or course not published |
| `409 Conflict` | Concurrency or inventory clash | Course inventory is lower than requested quantity |
| `500 Server Error` | Unhandled exception | Database connectivity failure or internal logic crash |
