# Credit Approval System

A Django-based REST API system for managing customer credit approvals, loan eligibility checks, and loan creation with automated credit scoring.

**🎉 Latest Update (Oct 21, 2025):** All API endpoints implemented! 37/37 tests passing ✅

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Credit-Approval-System-Django

# Install dependencies
uv sync

# Run migrations
uv run python manage.py migrate

# Ingest sample data
uv run python manage.py ingest_data

# Run API server
uv run python manage.py runserver

# Run tests
uv run python manage.py test test_api_endpoints
```

**API available at:** http://localhost:8000/api/

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Status](#project-status)
- [API Endpoints](#api-endpoints)
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
- Provides REST API endpoints for all operations

**Current Status**: **~92% Complete** (API Endpoints Implemented & Tested, Docker Ready)

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
- Credit Score Service (100-point algorithm with payment reliability multipliers)
- Loan Eligibility Service (with interest rate correction)
- Loan Creation Service (with atomic transactions)
- 37 comprehensive API endpoint tests (100% passing)

**REST API Endpoints (Phase 5) ✅**
- POST /api/customers/register - Customer registration with auto credit limit
- POST /api/loans/check-eligibility - Loan eligibility check with credit score
- POST /api/loans/create-loan - Loan creation with validation
- GET /api/loans/view-loan/{loan_id} - Single loan details
- GET /api/loans/view-loans/{customer_id} - Customer's loan history
- All endpoints fully tested and validated

### Recently Completed (October 21, 2025)

**API Endpoint Implementation**
- ✅ Implemented all 5 REST API endpoints
- ✅ Fixed field name consistency (`monthly_payment` vs `monthly_installment`)
- ✅ Fixed credit score calculation bugs (current year activity, payment reliability)
- ✅ All 37 API endpoint tests passing
- ✅ Credit score behavior tests validated (rejection thresholds, interest rate corrections)

**Credit Scoring Enhancements**
- ✅ Payment reliability multiplier system:
  - <30% on-time payments: 85% score penalty
  - 30-50% on-time: 65% penalty
  - 50-80% on-time: 50% penalty
- ✅ Fixed current year activity to include all loans (not just active)
- ✅ Corrected scoring for 5+ loans scenario

### Pending

**Phase 8: Docker Deployment** (Partially Complete)
- ✅ Dockerfile configured with uv package manager
- ✅ docker-compose.yml with Django, Redis, Celery services
- ⏳ Production deployment testing
- ⏳ Environment variable configuration

**Phase 9: Documentation & Polish**
- ⏳ API endpoint documentation (Swagger/OpenAPI)
- ⏳ Postman collection export
- ⏳ Production deployment guide
- ⏳ Performance optimization notes

---

## 🔌 API Endpoints

All endpoints are fully implemented and tested.

### Customer Management

**POST /api/customers/register**
- Register new customer with auto-calculated credit limit
- Returns: customer_id, approved_limit

```bash
curl -X POST http://localhost:8000/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "phone_number": "+1234567890",
    "monthly_income": 50000
  }'
```

### Loan Eligibility

**POST /api/loans/check-eligibility**
- Check loan eligibility with credit score calculation
- Returns: approval, credit_score, corrected_interest_rate, monthly_payment

```bash
curl -X POST http://localhost:8000/api/loans/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10.0,
    "term_months": 24
  }'
```

### Loan Management

**POST /api/loans/create-loan**
- Create approved loan with validation
- Returns: loan_id, loan_approved, monthly_payment

**GET /api/loans/view-loan/{loan_id}**
- Get single loan details
- Returns: Full loan information with customer details

**GET /api/loans/view-loans/{customer_id}**
- Get all loans for a customer
- Returns: List of loans with repayments_left

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
| **Phase 5** | API Endpoints | Complete ✅ | 100% |
| **Phase 7** | Testing | Complete ✅ | 100% |
| **Phase 8** | Docker | Partial | 80% |
| **Phase 9** | Documentation | Partial | 60% |
| **Overall** | | **Near Complete** | **~92%** |

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

### Run API Endpoint Tests

All API endpoints are validated with 37 comprehensive tests:

```bash
# Run all API endpoint tests
uv run python manage.py test test_api_endpoints
```

**Expected Output:**
```
Found 37 test(s).
Ran 37 tests in 0.3s
OK ✅
```

**Test Coverage:**
- Customer Registration API (5 tests)
- Loan Eligibility API (9 tests)
- Loan Creation API (10 tests)
- Loan Viewing APIs (6 tests)
- Credit Score Behavior (3 tests)
- EMI Constraint Validation (4 tests)

### Run Service Layer Tests

Business logic is covered by 32 service tests:

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
```

### Recent Test Fixes (October 21, 2025)

**Issues Fixed:**
1. ✅ **Field Name Mismatch** - Standardized `monthly_payment` across all services/serializers
2. ✅ **Credit Score Calculation** - Fixed loan count to use all loans (not just active)
3. ✅ **Payment Reliability System** - Added multiplier penalties for poor payment history:
   - <30% on-time payments → 85% score penalty
   - 30-50% on-time → 65% penalty
   - 50-80% on-time → 50% penalty
4. ✅ **Interest Rate Correction** - Now properly applies based on credit score bands
5. ✅ **Low Score Rejection** - Customers with score ≤10 correctly rejected

**Result:** All 37 API tests now passing (100% success rate)
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

### Immediate Priorities (8% Remaining)

**1. API Documentation (2-3 hours)**
- [ ] Add Swagger/OpenAPI documentation (drf-spectacular)
- [ ] Create API usage examples with curl commands
- [ ] Export Postman collection
- [ ] Document authentication flow (if adding)

**2. Docker Production Deployment (1-2 hours)**
- [ ] Test full docker-compose deployment
- [ ] Add environment variable management (.env file)
- [ ] Configure production settings (DEBUG=False, ALLOWED_HOSTS)
- [ ] Add health check endpoints
- [ ] Document deployment process

**3. Performance & Polish (1 hour)**
- [ ] Add database indexing for frequent queries
- [ ] Add API rate limiting
- [ ] Add request/response logging
- [ ] Add CORS headers for frontend integration
- [ ] Optimize credit score calculation queries

**4. Security Hardening (1 hour)**
- [ ] Add API authentication (Token/JWT)
- [ ] Add permission classes to views
- [ ] Add input sanitization
- [ ] Review security best practices

### Optional Enhancements

**Frontend Integration:**
- [ ] Create simple React/Vue dashboard
- [ ] Add loan application form
- [ ] Add customer dashboard with loan history

**Advanced Features:**
- [ ] Add loan payment tracking
- [ ] Add automated late payment penalties
- [ ] Add loan restructuring logic
- [ ] Add reporting/analytics endpoints

**Monitoring & Ops:**
- [ ] Add Prometheus metrics
- [ ] Add structured logging
- [ ] Add error tracking (Sentry)
- [ ] Add APM integration

---

## Recent Achievements (October 21, 2025)

### ✅ API Endpoints Implementation Complete
- Implemented all 5 REST API endpoints
- Fixed critical bugs in credit scoring logic
- Achieved 100% test pass rate (37/37 tests)

### ✅ Credit Scoring System Refinement
- Added payment reliability multiplier system
- Fixed loan count calculation to use all loans
- Corrected interest rate correction thresholds
- Validated score-based rejection logic

### ✅ Code Quality & Testing
- All API endpoints validated with comprehensive tests
- Fixed field naming inconsistencies
- Improved error handling and validation
- Added atomic transactions for loan creation

**Project Status:** Production-ready API, needs documentation and deployment polish

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

---

## Additional Documentation

- **FIX_PROPOSAL.md** - Analysis and fixes for API endpoint test failures
- **PHASE_5_PLAN.md** - Complete API implementation guide (now completed)
- **PROGRESS_COMPARISON.md** - Detailed progress tracking vs original plan
- **CELERY_GUIDE.md** - Celery setup and usage documentation
- **test_api_endpoints.py** - Complete API test suite with 37 tests

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

**Version:** 0.9.0 (Near Production Ready)  
**Last Updated:** October 21, 2025  
**Status:** 92% Complete - API Endpoints Implemented & Tested, Deployment Polish Pending