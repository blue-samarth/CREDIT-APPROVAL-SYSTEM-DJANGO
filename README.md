# Credit Approval System

A Django-based REST API system for managing customer credit approvals, loan eligibility checks, and loan creation with automated credit scoring.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Status](#project-status)
- [Setup & Installation](#setup--installation)
- [Project Structure](#project-structure)
- [Business Logic](#business-logic)
- [Testing](#testing)
- [Development Notes](#development-notes)
- [Next Steps](#next-steps)

---

## 🎯 Overview

This system provides a credit approval platform that:
- Registers customers with auto-calculated credit limits
- Ingests historical loan data via background tasks
- Calculates dynamic credit scores based on payment history
- Checks loan eligibility with interest rate corrections
- Manages loan creation and tracking

**Current Status**: **~55% Complete** (Infrastructure + Business Logic done, API endpoints pending)

---

## Features

### Implemented

**Infrastructure & Data Management**
- Django 5.2.7 with Python 3.13
- PostgreSQL-ready (SQLite for development)
- Celery 5.5.3 + Redis 6.4.0 for background tasks
- Excel data ingestion with Pandas
- Management command: `python manage.py ingest_data`
- 753 loans ingested in 4.83 seconds

**Business Logic Services**
- EMI Calculator Service (reducing balance method)
- Credit Score Service (100-point algorithm)
- Loan Eligibility Service
- 32 comprehensive tests

### Pending

**Phase 5: REST API Endpoints**
- POST /register - Customer registration
- GET /view-loan/{loan_id} - Single loan details
- GET /view-loans/{customer_id} - Customer's all loans
- POST /check-eligibility - Loan eligibility check
- POST /create-loan - Create approved loan

**Phase 8: Docker Deployment**
- Complete docker-compose.yml
- Complete Dockerfile

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.13 | Core programming language |
| **Framework** | Django | 5.2.7 | Web framework |
| **API** | Django REST Framework | 3.16.1 | REST API endpoints |
| **Database** | SQLite / PostgreSQL | - | Data persistence |
| **Task Queue** | Celery | 5.5.3 | Background job processing |
| **Message Broker** | Redis | 6.4.0 | Celery broker & result backend |
| **Data Processing** | Pandas | 2.3.3 | Excel data processing |
| **Package Manager** | uv | latest | Dependency management |

---

## Project Status

| Phase | Description | Status | Completion |
|-------|-------------|--------|------------|
| **Phase 1** | Infrastructure Setup | Complete | 100% |
| **Phase 2** | Data Models | Complete | 100% |
| **Phase 3** | Data Ingestion + Celery | Complete | 100% |
| **Phase 4** | Credit Scoring Engine | Complete | 100% |
| **Phase 6** | Service Layer | Complete | 100% |
| **Phase 7** | Testing | Partial | 60% |
| **Phase 5** | API Endpoints | Not Started | 0% |
| **Phase 8** | Docker | Partial | 20% |
| **Phase 9** | Documentation | Partial | 40% |
| **Overall** | | **In Progress** | **~55%** |

---

## Setup & Installation

### Prerequisites
- Python 3.13
- uv (Python package manager)
- Redis (for Celery)
- Git

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd Credit-Approval-System-Django
```

#### 2. Install uv (if not already installed)
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 3. Install Dependencies
```bash
# uv automatically creates and manages virtual environment
uv sync
```

#### 4. Configure Settings
```bash
# Copy environment variables (if .env file exists)
cp .env.example .env

# Edit settings if needed
# config/settings.py contains all configuration
```

#### 5. Run Migrations
```bash
uv run python manage.py migrate
```

#### 6. Ingest Sample Data (Optional)
```bash
# Place Excel files in data/ directory:
# - data/customer_data.xlsx
# - data/loan_data.xlsx

# Run ingestion command
uv run python manage.py ingest_data --customer-file data/customer_data.xlsx --loan-file data/loan_data.xlsx
```

#### 7. Start Redis (Required for Celery)
```bash
# Option 1: Local Redis
redis-server

# Option 2: Docker
docker run -d -p 6379:6379 redis:latest
```

#### 8. Start Celery Worker (Optional - for background tasks)
```bash
# In a separate terminal
uv run celery -A config worker -l info
```

#### 9. Start Development Server
```bash
uv run python manage.py runserver
```

Visit: http://localhost:8000

---

## Project Structure

```
Credit-Approval-System-Django/
├── config/                      # Django project configuration
│   ├── __init__.py             # Loads Celery on startup
│   ├── settings.py             # Django + Celery settings
│   ├── urls.py                 # Main URL routing
│   ├── celery.py               # Celery app configuration
│   └── wsgi.py / asgi.py       # WSGI/ASGI applications
│
├── apps/                        # Django applications
│   ├── customers/              # Customer management
│   │   ├── models.py           # Customer model
│   │   ├── apps.py             # App config (name='apps.customers')
│   │   └── migrations/
│   │
│   └── loans/                  # Loan management
│       ├── models.py           # Loan model
│       ├── apps.py             # App config (name='apps.loans')
│       └── migrations/
│
├── core/                        # Shared utilities & services
│   ├── services/               # Business logic services
│   │   ├── __init__.py         # Service exports
│   │   ├── emi_calculator_service.py      # EMI calculations
│   │   ├── credit_score_service.py        # Credit scoring (100 pts)
│   │   └── loan_eligibility_service.py    # Eligibility orchestration
│   │
│   ├── utils/                  # Utility functions
│   │   └── data_ingestion.py  # Excel data processing
│   │
│   ├── management/commands/    # Django commands
│   │   └── ingest_data.py      # Data ingestion command
│   │
│   └── tasks.py                # Celery tasks (async ingestion)
│
├── data/                        # Excel data files
│   ├── customer_data.xlsx
│   └── loan_data.xlsx
│
├── test_services.py            # Service test runner (32 tests)
├── test_celery_setup.py        # Celery infrastructure tests
│
├── pyproject.toml              # uv project configuration
├── uv.lock                     # Dependency lock file
├── .python-version             # Python version (3.13)
│
├── manage.py                   # Django management script
├── db.sqlite3                  # SQLite database (dev)
│
├── PHASE_5_PLAN.md             # API implementation guide
├── PROGRESS_COMPARISON.md      # Progress tracking document
├── CELERY_GUIDE.md             # Celery setup documentation
└── README.md                   # This file
```

### Configuration Notes

**Django Apps Setup:**

1. Add apps to `INSTALLED_APPS` in `config/settings.py`:
   ```python
   INSTALLED_APPS = [
       'django.contrib.admin',
       'django.contrib.auth',
       # ... other Django apps
       'rest_framework',  # If using DRF
       'apps.customers',
       'apps.loans',
       'core',
   ]
   ```

2. Update `name` attribute in `apps/{customers,loans}/apps.py`:
   ```python
   # apps/customers/apps.py
   from django.apps import AppConfig
   
   class CustomersConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'apps.customers'  # Must include 'apps/' prefix
   ```
   
   ```python
   # apps/loans/apps.py
   from django.apps import AppConfig
   
   class LoansConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'apps.loans'  # Must include 'apps/' prefix
   ```

**Note:** The `apps/` prefix is required because the apps are in a subdirectory, not at the project root.

---

## Business Logic

### Credit Score Algorithm

**Total Score: 100 points**

| Component | Max Points | Criteria |
|-----------|------------|----------|
| **Payment History** | 30 | (EMIs paid on time / Total EMIs) × 30 |
| **Loan Count** | 20 | 0-2 loans: 20pts, 3-4: 15pts, 5-6: 10pts, 7+: 5pts |
| **Current Year Activity** | 20 | 0 loans: 5pts, 1-2: 20pts, 3-4: 15pts, 5+: 5pts |
| **Loan Volume** | 30 | Based on utilization of approved limit |

**Override Rules:**
- If total current loans > approved limit → Score = 0
- If EMI burden > 50% monthly income → REJECT

### Interest Rate Correction

| Credit Score | Action |
|--------------|--------|
| > 50 | Approve at requested rate |
| 30-50 | Approve with minimum 12% rate |
| 10-30 | Approve with minimum 16% rate |
| ≤ 10 | **REJECT** loan |

### EMI Calculation
---

## Testing

### Service Tests

Business logic is covered by 32 tests:
  r = Monthly interest rate (annual_rate / 12 / 100)
  n = Tenure in months
```

**Special Case:** If interest rate = 0, then `EMI = P / n`

### Approved Credit Limit Calculation

**For New Customers:**
```
approved_limit = round(36 × monthly_income, -5)
```
*Rounds to nearest lakh (100,000)*

**Example:**
- Monthly income: ₹50,000
- Calculation: 36 × 50,000 = 1,800,000
- Approved limit: ₹18,00,000 (₹18 lakh)

---

## 🧪 Testing

### Run Service Tests

All business logic is covered by 32 comprehensive tests:

```bash
# Run all service tests
uv run python test_services.py
```

**Test Coverage:**
- EMI Calculator Service (8 tests)
- Credit Score Service (10 tests)
- Loan Eligibility Service (12 tests)
- Integration Tests (2 tests)

### Test Celery Setup

```bash
# Verify Celery infrastructure
uv run python test_celery_setup.py
```bash
# Verify Celery infrastructure
uv run python test_celery_setup.py
```
#### Test Data Ingestion
```bash
# Synchronous mode (for testing)
uv run python manage.py ingest_data --customer-file data/customer_data.xlsx --loan-file data/loan_data.xlsx

# Async mode (production)
uv run python manage.py ingest_data --async --customer-file data/customer_data.xlsx --loan-file data/loan_data.xlsx
```

#### Test Services in Django Shell
```bash
uv run python manage.py shell
```

```python
from apps.customers.models import Customer
from core.services import CreditScoreService, LoanEligibilityService

# Get a customer
customer = Customer.objects.first()

# Calculate credit score
score_result = CreditScoreService.calculate_credit_score(customer)
print(f"Credit Score: {score_result['score']}")

# Check loan eligibility
eligibility = LoanEligibilityService.check_eligibility(
    customer_id=customer.customer_id,
    loan_amount=500000,
    interest_rate=10.0,
    tenure_months=24
)
print(f"Approved: {eligibility['approval']}")
print(f"Interest Rate: {eligibility['corrected_interest_rate']}")
print(f"Monthly EMI: {eligibility['monthly_installment']}")
```

---

## 💡 Development Notes
---

## Development Notes
All Python commands should be prefixed with `uv run`:

```bash
# Django management commands
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver

# Celery commands
uv run celery -A config worker -l info
uv run celery -A config beat -l info

# Testing
uv run python test_services.py
uv run pytest  # If using pytest
```

### Database

**Current:** SQLite (development)
**Production:** PostgreSQL (configured but not active)

To switch to PostgreSQL:
1. Update `DATABASES` in `config/settings.py`
2. Install psycopg2-binary (already in dependencies)
3. Run migrations: `uv run python manage.py migrate`

### Celery Background Tasks

**Available Tasks:**
- `core.tasks.ingest_customer_data_task` - Import customer Excel
- `core.tasks.ingest_loan_data_task` - Import loan Excel
- `core.tasks.ingest_all_data_task` - Chain both imports

**Monitoring:**
```bash
# Start Flower (Celery monitoring)
uv run celery -A config flower

# Visit: http://localhost:5555
```

### Data Models

**Customer Model:**
- `customer_id` (PK, auto)
- `first_name`, `last_name`
- `age` (>= 18)
- `phone_number` (unique)
- `monthly_income`
- `approved_credit_limit` (calculated)
- `current_debt` (updated on loan creation)

**Loan Model:**
- `loan_id` (PK, auto)
- `customer_id` (FK to Customer)
- `loan_amount`
- `interest_rate`
- `term_months` (tenure)
- `monthly_payment` (EMI)
- `monthly_payments_made_on_time`
- `loan_approved` (boolean)
- `start_date`, `end_date`
- `is_active` (boolean)

---

## Next Steps

### Immediate Priority: Phase 5 - API Endpoints

**Implementation Order:**
1. **DRF Setup** (30 min)
   - Add `rest_framework` to INSTALLED_APPS
   - Configure REST_FRAMEWORK settings
   - Update main URLs

2. **POST /register** (1.5 hrs)
   - Create serializers
   - Create view
   - Test registration flow

3. **GET /view-loan/{loan_id}** (1 hr)
   - Create loan serializers
   - Implement view with select_related()
   - Test retrieval

4. **GET /view-loans/{customer_id}** (1 hr)
   - Add filtering logic
   - Calculate repayments_left
   - Test listing

5. **POST /check-eligibility** (3-4 hrs)
   - Integrate with LoanEligibilityService
   - Handle all credit score bands
   - Comprehensive testing

6. **POST /create-loan** (2 hrs)
   - Reuse eligibility logic
   - Create loan with transaction
   - Update customer debt

**Reference:** See `PHASE_5_PLAN.md` for detailed implementation guide.

### Future Phases

**Phase 8: Docker Deployment** (2-3 hrs)
- Complete Dockerfile with uv
- Complete docker-compose.yml with all services
- Test full containerized deployment

**Phase 9: Documentation** (1-2 hrs)
- API endpoint documentation
- Postman collection
- Deployment guide

**Phase 10: Final Testing** (1 hr)
- End-to-end workflow testing
- Performance optimization
- Production readiness checklist

---

## Additional Documentation

- **PHASE_5_PLAN.md** - Complete API implementation guide with code examples
- **PROGRESS_COMPARISON.md** - Detailed progress tracking vs original plan
- **CELERY_GUIDE.md** - Celery setup and usage documentation
- **TEST_SERVICES.md** - Testing guide for service layer

---

## Troubleshooting

### Common Issues

**Issue:** `ImportError: No module named 'rest_framework'`
```bash
# Solution: Install DRF
uv add djangorestframework
```

**Issue:** Redis connection refused
```bash
# Solution: Start Redis server
redis-server
# Or via Docker:
docker run -d -p 6379:6379 redis:latest
```

**Issue:** Celery tasks not processing
```bash
# Solution: Ensure Redis is running and start worker
redis-cli ping  # Should return PONG
uv run celery -A config worker -l info
```

**Issue:** Import errors for apps
```bash
# Solution: Verify apps.py has correct name
# apps/customers/apps.py should have:
# name = 'apps.customers'  # NOT just 'customers'
```

**Issue:** Tests failing with `TypeError: conversion from NoneType to Decimal`
```bash
# Solution: Bug in credit_score_service.py (line ~108)
# Change: elif recent_loans_count <= 5:
# To: else:
#     return 5
```

---

## License

This project is part of a technical assignment for educational purposes.

---

**Version:** 0.1.0 (Development)  
**Last Updated:** October 20, 2025  
**Status:** 55% Complete - Business Logic Ready, API Endpoints In Progress