# 📚 Library Borrowing & Membership Management System

A modern, comprehensive library management system built with **FastAPI** and **PostgreSQL**. This system provides complete solutions for library operations including intelligent member management, automated book circulation, smart reservation queuing, and real-time notifications.

## ✨ Features

### 🔐 Authentication & Authorization
- User registration and login with JWT authentication
- Argon2 password hashing (RFC 9106 compliant)
- Three-tier role-based access control (RBAC): ADMIN, LIBRARIAN, MEMBER
- Session management with 720-minute token expiry

### 👥 Member Management
- Complete member lifecycle management (application → approval → active → frozen)
- Member profile management with student ID and card number
- Admin approval workflow for new member applications
- Member freeze/unfreeze with reason tracking
- Membership validity period management

### 📖 Book Circulation System
- Borrow/return workflow with automatic due date calculation (14 days)
- Renewal mechanism (max 1 renewal per loan, +14 days)
- Active loan limit per member (≤ 5 books)
- Automatic late fee calculation (¥1/day, max ¥50)
- Complete borrowing history tracking

### 🎫 Reservation System
- Queue-based reservation system (FIFO principle)
- Automatic upgrade to "ready for pickup" when copy becomes available
- 48-hour pickup deadline management
- Automatic expiration of overdue reservations
- Reservation history and status tracking

### 💰 Fine Management
- Automatic overdue fine calculation (¥1/day, max ¥50)
- Special fines for damaged books (¥20) and lost books (¥50)
- Fine payment tracking and status management
- Fine statistics and reporting

### 🔔 Notification System
- Automatic due date reminders (9:00 AM daily)
- Overdue reminders (9:05 AM daily)
- Reservation status updates
- Notification status tracking (unread/read/dismissed)
- Multi-type notification support

### 🔍 Advanced Search
- Multi-dimensional search by ISBN, title, author, category
- Smart matching: exact match priority → fuzzy match → ISBN fragment match
- Category-based filtering and sorting
- Pagination support

### 📊 Admin Functions
- Comprehensive book management (CRUD, categorization, ISBN deduplication)
- Copy/barcode management and location tracking
- User role assignment
- Announcement publishing and management
- Complete audit logging of all operations
- Customizable reminder policies
- Data reporting and statistics

### 📋 Other Features
- Responsive HTML templates with Jinja2
- CORS support for multi-origin requests
- Complete API error handling with meaningful messages
- Full audit trail for compliance
- Sample data seeding for demonstration (1000 books)

---

## 🛠️ Technology Stack

### Backend
| Component | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.116.0+ | Web framework |
| **Python** | 3.12+ | Language |
| **SQLAlchemy** | 2.0.41+ | ORM |
| **Psycopg** | 3.2.9+ | PostgreSQL adapter |
| **Pydantic** | 2.11.0+ | Data validation |
| **PyJWT** | 2.10.0+ | JWT tokens |
| **Argon2-cffi** | 25.1.0+ | Password hashing |
| **APScheduler** | 3.11.0+ | Task scheduling |
| **Uvicorn** | 0.35.0+ | ASGI server |

### Frontend
| Component | Version |
|-----------|---------|
| **Vite** | 7.1.7+ |
| **JavaScript** | Vanilla |
| **Jinja2** | 3.1.6+ |

### Database
| Component | Version |
|-----------|---------|
| **PostgreSQL** | 12+ |

### Testing & Development
| Component | Version |
|-----------|---------|
| **Pytest** | 8.4.0+ |
| **HTTPx** | 0.28.1+ |
| **Ruff** | 0.15.10+ |

---

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (package manager)
- Docker (for PostgreSQL)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/hkmu-comp3510sef-2026-024/src.git
cd src
```

### Step 2: Start PostgreSQL with Docker

```bash
docker run -d --name library-postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=library_system \
  -p 5432:5432 \
  postgres:16

# Create app user and set ownership
docker exec -i library-postgres psql "postgresql://postgres:postgres123@localhost:5432/postgres" \
  -c "CREATE USER library_app WITH LOGIN PASSWORD 'library_app_123';"
docker exec -i library-postgres psql "postgresql://postgres:postgres123@localhost:5432/postgres" \
  -c "ALTER DATABASE library_system OWNER TO library_app;"
```

### Step 3: Install Dependencies
```bash
uv sync
```

### Step 4: Configure Environment Variables (optional)

Defaults point to Docker PostgreSQL on port 5432. Override if needed:

```bash
# Database Configuration
LIBRARY_DB_HOST=localhost
LIBRARY_DB_PORT=5432
LIBRARY_DB_NAME=library_system
LIBRARY_DB_USER=library_app
LIBRARY_DB_PASSWORD=library_app_123

# Application Configuration
LIBRARY_SECRET_KEY=your-super-secret-key-change-this-in-production
LIBRARY_ACCESS_TOKEN_EXPIRE_MINUTES=720

# Business Logic Configuration
LIBRARY_BORROW_DAYS=14
LIBRARY_RENEW_DAYS=14
LIBRARY_MAX_RENEWALS=1
LIBRARY_MAX_ACTIVE_LOANS=5
LIBRARY_PICKUP_HOURS=48
LIBRARY_FINE_PER_DAY=1
LIBRARY_MAX_FINE=50
LIBRARY_LOST_FINE_AMOUNT=50
LIBRARY_DAMAGED_FINE_AMOUNT=20
LIBRARY_GRACE_PERIOD_DAYS=0

# Feature Flags
LIBRARY_ENABLE_SCHEDULER=1
LIBRARY_ENABLE_SAMPLE_CATALOG=1
LIBRARY_SAMPLE_CATALOG_TARGET=1000
```

### Step 5: Run Database Initialization

**Windows (PowerShell):**
```powershell
$env:LIBRARY_DB_PORT="5432"; uv run python main.py
```

**macOS / Linux:**
```bash
uv run python main.py
```

This creates all tables and seeds default data on first run.

---

## 🚀 Quick Start

### Running the Development Server

**Windows (PowerShell):**
```powershell
$env:LIBRARY_DB_PORT="5432"; uv run python main.py
```

**macOS / Linux:**
```bash
uv run python main.py
```

Server will be available at http://localhost:8000

### Access the Application

- **Frontend**: http://localhost:8000 (HTML pages served by FastAPI)
- **Admin Panel**: http://localhost:8000/admin/portal
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

### Default Admin Credentials

```
Email: admin@example.com
Password: admin123
```

⚠️ **Change the default password immediately in production!**

---

## 📁 Project Structure

```
src/                               # Repository root (git root)
├── app/                           # Main application package
│   ├── __init__.py
│   ├── application.py             # FastAPI app configuration
│   ├── config.py                  # Configuration settings
│   ├── database.py                # Database setup and session management
│   ├── dependencies.py            # Dependency injection
│   ├── enums.py                   # Enumeration definitions
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── postgres_setup.py          # PostgreSQL initialization
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── services.py                # Business logic layer
│   ├── utils.py                   # Utility functions
│   ├── web.py                     # Template configuration
│   ├── routers/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── admin.py              # Admin endpoints
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── member.py             # Member endpoints
│   │   └── public.py             # Public endpoints
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── admin/
│   │   ├── auth/
│   │   ├── member/
│   │   └── public/
│   └── data/
│       └── catalog_seed.json     # Sample book data
├── frontend/                      # Frontend (Vite)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.mjs
│   ├── static/
│   └── [page folders]/
├── tests/                         # Test suite
│   └── test_library_system.py
├── pyproject.toml                # Project configuration
├── main.py                       # Application entry point
└── README.md                     # This file
```

---

## 🔌 API Endpoints

### Authentication
```
POST    /auth/register          # User registration
POST    /auth/login             # User login
POST    /auth/logout            # Logout
```

### Member Operations
```
GET     /me                     # Get current user profile (includes membership + profile data)
GET     /me/loans               # Get current loans and borrowing history
POST    /loans/borrow           # Borrow a book (body: { bookId, copyId })
POST    /loans/{loan_id}/renew  # Renew a loan
GET     /me/reservations        # Get reservations
POST    /reservations           # Create reservation (body: { bookId })
DELETE  /reservations/{id}      # Cancel reservation
GET     /me/notifications       # Get notifications
POST    /me/notifications/{id}/read  # Mark notification as read (body: { read: true/false })
GET     /books/{book_id}/available-copies  # List available copies of a book
GET     /recommendations        # Get book recommendations
```

### Admin Operations
```
# User Management
GET     /admin/users            # List all users
PUT     /admin/users/{user_id}/role  # Update user role

# Book Management
GET     /admin/books            # List all books
POST    /admin/books            # Add new book
PUT     /admin/books/{book_id}  # Update book

# Copy Management
GET     /admin/copies           # List copies
POST    /admin/copies           # Add copy
PUT     /admin/copies/{copy_id} # Update copy
PUT     /admin/copies/{copy_id}/status  # Update copy status

# Member Management
GET     /admin/members          # List members
POST    /admin/members/{user_id}/approve   # Approve membership
POST    /admin/members/{user_id}/freeze    # Freeze membership
POST    /admin/members/{user_id}/unfreeze  # Unfreeze membership
POST    /admin/members/{user_id}/renew      # Renew membership

# Circulation
GET     /admin/loans            # List all loans
POST    /admin/loans/checkout   # Admin checkout (body: { userId, bookId, copyId, barcode })
POST    /admin/loans/{loan_id}/checkin  # Admin checkin (body: { condition })

# Fine Management
GET     /admin/fines            # List fines
POST    /admin/fines/{fine_id}/mark-paid  # Mark fine as paid (body: { waived: false })

# Audit & Policy
GET     /admin/auditlogs        # Audit trail
GET     /admin/reminder-policy  # Get reminder policy
PUT     /admin/reminder-policy  # Update reminder policy

# Announcements
GET     /admin/announcements    # List announcements
POST    /admin/announcements    # Create announcement
PUT     /admin/announcements/{announcement_id}  # Update announcement

# Reports
GET     /admin/dashboard        # Dashboard stats
GET     /admin/reports/summary  # Summary report

# HTML Pages (admin portal)
GET     /admin/portal           # Admin portal page
GET     /admin/members-page     # Members management page
GET     /admin/books-page       # Book management page
GET     /admin/copies-page      # Copy management page
GET     /admin/circulation-page # Circulation page
GET     /admin/fines-page       # Fines page
GET     /admin/auditlogs-page   # Audit logs page
GET     /admin/reminder-policy-page  # Reminder policy page
GET     /admin/reports-page     # Reports page
GET     /admin/users-page       # User management page
GET     /admin/announcements-page   # Announcements page
```

### Public API
```
GET     /public/catalog         # Search books (public)
GET     /public/books/:id       # Book details (public)
```

---

## 🗄️ Database Schema

### Core Tables
- **users** - User accounts
- **member_profiles** - Member personal information
- **memberships** - Member status management
- **books** - Book catalog
- **copies** - Individual book copies
- **loans** - Borrowing records
- **reservations** - Book reservations
- **fines** - Fine tracking
- **notifications** - User notifications
- **announcements** - Library announcements
- **audit_logs** - Operation audit trail
- **reminder_policies** - Customizable reminder rules

### Key Relationships
```
users ──→ member_profiles
       ├→ memberships
       └→ audit_logs

books ──→ copies ──→ loans ──→ fines
                  └→ reservations
```

---

## 📊 Business Configuration

### Borrowing Rules
- Borrow period: 14 days (configurable)
- Maximum active loans: 5 books per member
- Renewal allowed: 1 time, +14 days
- Grace period: 0 days (configurable)

### Fine Structure
- Overdue fee: ¥1 per day
- Maximum fine: ¥50
- Damaged book compensation: ¥20
- Lost book compensation: ¥50

### Automation
- Due date reminders: 9:00 AM daily (3 days before due)
- Overdue reminders: 9:05 AM daily
- Expired reservation cleanup: Every 30 minutes
- Sample data seeding: On application startup

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_library_system.py

# Run with coverage report
pytest --cov=app tests/

# Run specific test
pytest tests/test_library_system.py::test_member_registration
```

### Test Database
Tests use a separate PostgreSQL database (`library_system_test`) to avoid affecting production data.

Configure test database:
```bash
export LIBRARY_TEST_DATABASE_URL=postgresql+psycopg://library_app:library_app_123@localhost:5432/library_system_test
```

---

## 🔄 Automated Tasks

The system includes scheduled tasks managed by APScheduler:

| Task | Schedule | Function |
|------|----------|----------|
| Due Reminders | 9:00 AM daily | Generate notifications for books due in 3 days |
| Overdue Reminders | 9:05 AM daily | Generate notifications for overdue books |
| Reservation Cleanup | Every 30 minutes | Remove expired reservations |
| Admin Seeding | App startup | Create default admin if not exists |
| Sample Catalog | App startup | Load 1000 sample books for testing |

---

## 🐛 Troubleshooting

### Issue: "Database connection refused"
```powershell
# Verify PostgreSQL is running
docker ps --filter name=library-postgres

# Check environment variables
echo $env:LIBRARY_DATABASE_URL

# Test database connection
docker exec -i library-postgres psql "postgresql://library_app:library_app_123@localhost:5432/library_system" -c "SELECT 1;"
```

### Issue: "Port 8000 already in use"
```bash
# Change port in main.py
# Port: 8001
# Or kill the process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Issue: "Can't find module 'app'"
```bash
# Install in development mode
uv sync
```

---

**Last Updated**: April 2026
