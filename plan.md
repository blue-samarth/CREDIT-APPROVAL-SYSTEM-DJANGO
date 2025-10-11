# Credit Approval System - Technical Implementation Plan

## Project Overview
**Duration**: 36 hours  
**Tech Stack**: Django 4+, DRF, PostgreSQL, Celery, Redis, Docker  
**Estimated Effort**: 22-26 hours of focused work

---

## Phase 1: Infrastructure Setup (2-3 hours)

### 1.1 Project Initialization with uv

**Setup Steps**:
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize uv project
uv init credit-approval-system
cd credit-approval-system

# Set Python version
echo "3.11" > .python-version

# Add dependencies
uv add django djangorestframework psycopg2-binary
uv add celery redis python-decouple
uv add openpyxl pandas gunicorn

# Create Django project (using uv run)
uv run django-admin startproject config .

# Create app directories
uv run python manage.py startapp customers
uv run python manage.py startapp loans
mv customers apps/
mv loans apps/
```

**pyproject.toml Structure**:
```toml
[project]
name = "credit-approval-system"
version = "0.1.0"
description = "Credit approval system with Django"
requires-python = ">=3.11"
dependencies = [
    "django>=4.2,<5.0",
    "djangorestframework>=3.14",
    "psycopg2-binary>=2.9",
    "celery>=5.3",
    "redis>=5.0",
    "python-decouple>=3.8",
    "openpyxl>=3.1",
    "pandas>=2.1",
    "gunicorn>=21.2",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4",
    "pytest-django>=4.5",
]
```

**Benefits of uv**:
- **Speed**: 10-100x faster than pip for installs
- **Lock file**: `uv.lock` ensures reproducible builds across machines
- **No venv management**: uv handles virtual environments automatically
- **Docker optimization**: Better layer caching with uv
- **Conflict resolution**: Better dependency resolver than pip

### 1.2 Project Structure
```
credit-approval-system/
├── docker-compose.yml          # Orchestrate all services
├── Dockerfile                  # Django app container
├── pyproject.toml              # uv project configuration
├── uv.lock                     # Locked dependencies
├── .python-version             # Python version (3.11)
├── config/                     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py              # Celery configuration
├── apps/
│   ├── customers/             # Customer domain
│   └── loans/                 # Loan domain
├── core/                      # Shared utilities
│   └── management/commands/   # Data ingestion command
└── data/                      # Excel files
```

### 1.2 Docker Services Architecture
- **PostgreSQL**: Primary database (port 5432)
- **Redis**: Celery broker & result backend (port 6379)
- **Django Web**: REST API server (port 8000)
- **Celery Worker**: Background task processor

**Key Decision**: Use health checks in docker-compose to ensure proper service startup order (DB → Redis → Web → Celery)

### 1.3 Dependencies Strategy (using `uv`)
- **uv**: Ultra-fast Python package installer and resolver
- **Django 4.2** + **DRF 3.14**: Core framework
- **psycopg2-binary**: PostgreSQL adapter
- **celery + redis**: Background tasks
- **openpyxl/pandas**: Excel parsing (pandas for robust data handling)
- **python-decouple**: Environment config management

**Why uv?**
- 10-100x faster than pip for installs
- Better dependency resolution
- Built-in virtual environment management
- Lock file for reproducible builds

---

## Phase 2: Data Model Design (2-3 hours)

### 2.1 Customer Model
**Table**: `customers`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| customer_id | AutoField (PK) | Primary Key | Auto-generated |
| first_name | CharField(100) | NOT NULL | |
| last_name | CharField(100) | NOT NULL | |
| age | IntegerField | >= 18 | Validation |
| phone_number | CharField(15) | UNIQUE, NOT NULL | Index for lookups |
| monthly_salary | Decimal(12,2) | >= 0 | Precision for money |
| approved_limit | Decimal(15,2) | >= 0 | Higher precision |
| current_debt | Decimal(15,2) | DEFAULT 0 | Calculated field |

**Indexes**: 
- `phone_number` (unique lookups)
- `customer_id` (PK already indexed)

**Business Logic**:
- `approved_limit` calculation in registration endpoint
- `current_debt` updated when loans are created

### 2.2 Loan Model
**Table**: `loans`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| loan_id | AutoField (PK) | Primary Key | Auto-generated |
| customer | ForeignKey | ON DELETE CASCADE | Related name: 'loans' |
| loan_amount | Decimal(15,2) | >= 0 | |
| tenure | IntegerField | >= 1 | In months |
| interest_rate | Decimal(5,2) | 0-100 | Annual percentage |
| monthly_repayment | Decimal(12,2) | >= 0 | EMI amount |
| emis_paid_on_time | IntegerField | >= 0 | For credit score |
| start_date | DateField | NOT NULL | Loan start |
| end_date | DateField | NOT NULL | Loan maturity |
| loan_approved | BooleanField | DEFAULT False | Approval status |

**Indexes**:
- Composite: `(customer_id, loan_approved)` - for active loan queries
- `(start_date, end_date)` - for date range queries

**Computed Properties**:
- `repayments_left`: Calculate from current date vs end_date
- `is_active`: Check if loan is currently running

### 2.3 Database Optimization Strategy
- Use `select_related('customer')` for loan queries to avoid N+1
- Aggregate queries for credit score calculation
- Consider adding `db_index=True` on frequently queried fields

---

## Phase 3: Data Ingestion Strategy (3-4 hours)

### 3.1 Celery Task Architecture

**Two separate tasks**:
1. `ingest_customer_data(file_path)` - Reads customer Excel
2. `ingest_loan_data(file_path)` - Reads loan Excel (depends on customers)

**Why Celery?**
- Assignment requires background workers
- Allows async processing of large datasets
- Can monitor task progress/failures

### 3.2 Data Processing Pipeline

```
Excel File → Pandas DataFrame → Data Cleaning → Bulk Insert → Database
```

**Data Cleaning Steps**:
1. Strip whitespace from column names
2. Convert to lowercase, replace spaces with underscores
3. Handle missing values (use defaults)
4. Type casting with error handling
5. Date parsing for loan data

**Transaction Handling**:
- Wrap each file ingestion in `transaction.atomic()`
- If error occurs, rollback entire file
- Log failures for debugging

### 3.3 Management Command Design

**Command**: `python manage.py ingest_data`

**Options**:
- `--customer-file`: Path to customer Excel
- `--loan-file`: Path to loan Excel  
- `--async`: Use Celery (default: synchronous for testing)

**Execution Strategy**:
- First run: Synchronous mode to verify data integrity
- Production: Async mode for performance

**Idempotency**: Use `update_or_create()` to allow re-running without duplicates

---

## Phase 4: Credit Scoring Engine (3-4 hours)

### 4.1 Credit Score Algorithm

**Total Score**: 100 points (breakdown below)

#### Component 1: Payment History (30 points)
```
score = (total_emis_paid_on_time / total_emis_across_all_loans) * 30
```
- Perfect payment: 30 points
- 90% on-time: 27 points
- 50% on-time: 15 points

#### Component 2: Number of Loans (20 points)
```
0-2 loans: 20 points
3-4 loans: 15 points
5-6 loans: 10 points
7+ loans: 5 points
```
Rationale: Fewer loans = lower risk

#### Component 3: Current Year Activity (20 points)
```
No activity: 5 points (inactive)
1-2 loans: 20 points (optimal)
3-4 loans: 15 points (moderate)
5+ loans: 10 points (high activity = risk)
```
Check: `start_date.year == current_year OR end_date.year == current_year`

#### Component 4: Loan Volume (30 points)
```
volume_ratio = total_loan_amount / approved_limit

ratio <= 0.5: 30 points (low utilization)
ratio <= 1.0: 25 points (moderate)
ratio <= 1.5: 15 points (high)
ratio > 1.5: 5 points (very high)
```

#### Critical Override Rules
1. **If `sum(current_loans) > approved_limit`: score = 0**
2. **If `sum(active_EMIs) > 50% of monthly_salary`: REJECT regardless of score**

### 4.2 Interest Rate Correction Logic

**Credit Score Bands**:
```
Score > 50  → Any interest rate (approve)
50 >= Score > 30 → Minimum 12% (if requested < 12%, correct to 12%)
30 >= Score > 10 → Minimum 16% (if requested < 16%, correct to 16%)
Score <= 10 → REJECT (no interest rate)
```

**Return Values**:
- `approval`: boolean
- `corrected_interest_rate`: adjusted rate or original rate
- `interest_rate`: original requested rate

### 4.3 EMI Calculation Method

**Formula**: Reducing Balance Method (Compound Interest)
```
EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)

Where:
P = Principal (loan_amount)
r = Monthly rate (annual_rate / 12 / 100)
n = Tenure in months
```

**Edge Cases**:
- If interest_rate = 0: `EMI = principal / tenure`
- If tenure = 0: Return 0 (validation should prevent this)

**Precision**: Round to 2 decimal places using `Decimal.quantize()`

---

## Phase 5: API Endpoints (8-10 hours)

### 5.1 POST /register

**Purpose**: Create new customer with calculated approved limit

**Business Logic**:
1. Validate input (unique phone, age >= 18)
2. Calculate: `approved_limit = round(36 * monthly_income, -5)` (nearest lakh)
3. Set `current_debt = 0` for new customers
4. Return customer details with generated ID

**Error Handling**:
- 400: Validation errors (duplicate phone, invalid age)
- 500: Database errors

**Time**: 1.5 hours

---

### 5.2 POST /check-eligibility

**Purpose**: Check if customer qualifies for loan (without creating it)

**Processing Flow**:
```
1. Validate customer exists
2. Calculate credit score (CreditScoreService)
3. Check EMI constraint (current_EMIs <= 50% salary)
4. Determine approval based on credit score
5. Correct interest rate if needed
6. Calculate EMI
7. Return eligibility response
```

**Response Logic**:
- `approval = True/False` based on credit score bands
- `interest_rate` = original requested
- `corrected_interest_rate` = adjusted rate (or same if valid)
- `monthly_installment` = calculated EMI

**Edge Cases**:
- Customer doesn't exist: 404
- EMI constraint violated: `approval = False`
- Score <= 10: `approval = False`

**Time**: 3-4 hours (most complex)

---

### 5.3 POST /create-loan

**Purpose**: Actually create a loan if eligible

**Processing Flow**:
```
1. Run same eligibility check as /check-eligibility
2. If approved:
   - Create Loan object with corrected interest rate
   - Set start_date = today
   - Set end_date = today + tenure months
   - Set loan_approved = True
   - Update customer.current_debt
3. If rejected:
   - Return rejection message
   - loan_id = None
```

**Important**: Reuse eligibility logic from service layer (DRY principle)

**Response**:
- `loan_id`: Generated ID or null
- `loan_approved`: boolean
- `message`: "Loan approved" or rejection reason
- `monthly_installment`: EMI amount

**Time**: 2 hours

---

### 5.4 GET /view-loan/{loan_id}

**Purpose**: Retrieve single loan details with customer info

**Query Optimization**:
```python
Loan.objects.select_related('customer').get(loan_id=loan_id)
```
Prevents N+1 query issue

**Response Structure**:
```json
{
  "loan_id": 123,
  "customer": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "9876543210",
    "age": 30
  },
  "loan_amount": 500000,
  "interest_rate": 12.5,
  "monthly_installment": 45000,
  "tenure": 12
}
```

**Error Handling**:
- 404: Loan not found

**Time**: 1 hour

---

### 5.5 GET /view-loans/{customer_id}

**Purpose**: List all loans for a customer

**Query**:
```python
Loan.objects.filter(customer_id=customer_id, loan_approved=True)
```

**Computed Field**: `repayments_left`
- Calculate in model property or annotate in queryset
- Formula: `tenure - months_elapsed` (bounded by 0)

**Response**: Array of loan objects (same structure as view-loan minus customer)

**Optimization**: Add pagination if customer has many loans (bonus)

**Time**: 1 hour

---

## Phase 6: Service Layer Architecture (2 hours)

### 6.1 Separation of Concerns

**Why Service Layer?**
- Keep views thin (only handle HTTP)
- Reusable business logic
- Easier to test
- Single source of truth

**Service Classes**:

#### `CreditScoreService`
- `calculate_credit_score(customer_id)` → int
- `check_emi_constraint(customer_id)` → bool, Decimal
- `get_corrected_interest_rate(score, requested_rate)` → bool, Decimal
- `calculate_emi(principal, rate, tenure)` → Decimal

#### `LoanEligibilityService`
- `check_eligibility(customer_id, loan_amount, interest_rate, tenure)` → dict
- Orchestrates all credit checks
- Returns comprehensive eligibility data

#### `LoanCreationService`
- `create_loan(customer_id, loan_amount, interest_rate, tenure)` → Loan or None
- Handles loan creation transaction
- Updates customer debt

### 6.2 Error Handling Strategy

**Custom Exceptions**:
- `CustomerNotFoundException`
- `LoanNotFoundException`
- `EligibilityCheckFailedException`

**DRF Exception Handler**:
- Catch exceptions in views
- Return consistent error format
- Log errors for debugging

---

## Phase 7: Testing Strategy (2-3 hours)

### 7.1 Manual Testing Checklist

**Use Postman/cURL**:
1. Register 3-4 customers with varying incomes
2. Create loans with different credit scenarios
3. Test edge cases:
   - Customer with no loan history
   - Customer exceeding approved limit
   - Customer with 50%+ EMI burden
   - Invalid loan_id/customer_id

### 7.2 Unit Tests (Bonus)

**Priority Tests**:
1. Credit score calculation with mock data
2. EMI calculation accuracy
3. Interest rate correction logic
4. Eligibility check scenarios

**Framework**: Django TestCase + DRF APITestCase

**Time**: 2-3 hours if attempting bonus

---

## Phase 8: Docker & Deployment (2 hours)

### 8.1 Docker Best Practices

**Dockerfile**:
- Use `python:3.11-slim` (smaller image)
- Multi-stage build (optional, if time permits)
- Non-root user for security
- Health check endpoint

**docker-compose.yml**:
- Service dependencies with `depends_on` + health checks
- Named volumes for data persistence
- Environment variables for configuration
- Restart policies

### 8.2 Deployment Checklist

**Test Command**:
```bash
# Build and start all services
docker-compose up --build

# Run data ingestion
docker-compose exec web uv run python manage.py ingest_data

# Check service status
docker-compose ps
```

**Verification Steps**:
1. All services start without errors
2. Database migrations run automatically
3. Data ingestion completes successfully
4. All API endpoints respond correctly
5. Celery worker processes tasks

**Quick API Tests**:
```bash
# Test registration
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","age":30,"monthly_income":50000,"phone_number":"9876543210"}'

# Test view loans
curl http://localhost:8000/view-loans/1
```

### 8.3 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| DB connection refused | Add health check + wait-for-it.sh |
| Celery not picking tasks | Check Redis connection, restart worker |
| Migration errors | Run `makemigrations` before migrate |
| Import errors | Check `__init__.py` in all packages |

---

## Phase 9: Documentation (1-2 hours)

### 9.1 README Structure

```markdown
# Credit Approval System

## Setup
- Prerequisites: Docker, Docker Compose
- No local Python/uv installation needed (handled by Docker)

## Running the Application
```bash
# Start all services
docker-compose up --build

# Run data ingestion
docker-compose exec web uv run python manage.py ingest_data

# Access API
http://localhost:8000

# View logs
docker-compose logs -f web
```

## Local Development (with uv)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo>
cd credit-approval-system

# Install dependencies (uv handles venv automatically)
uv sync

# Run migrations
uv run python manage.py migrate

# Start dev server
uv run python manage.py runserver
```

## API Documentation
- Endpoint list with examples
- Request/response formats
- Error codes

## Architecture
- High-level diagram
- Technology choices
- Design decisions

## Assumptions
- Credit score algorithm details
- EMI calculation method
- Edge case handling
```

### 9.2 Code Documentation

**Docstrings**: Add to all service methods explaining:
- Purpose
- Parameters
- Return values
- Edge cases

**Comments**: Explain complex business logic (credit score, EMI calc)

---

## Phase 10: Final Checklist (1 hour)

### 10.1 Pre-Submission Verification

- [ ] `docker-compose up --build` works from scratch
- [ ] All 6 endpoints return correct responses
- [ ] Data ingestion completes without errors
- [ ] No hardcoded values (use environment variables)
- [ ] Code is clean and organized
- [ ] README has clear setup instructions
- [ ] Git history shows incremental progress
- [ ] `.gitignore` excludes `.venv/`, `uv.lock` committed
- [ ] `pyproject.toml` has all dependencies
- [ ] Both `pyproject.toml` and `uv.lock` are committed

**uv-specific checks**:
- [ ] `.python-version` file exists
- [ ] `uv sync` works on fresh clone
- [ ] Docker build uses uv correctly
- [ ] All commands in README use `uv run` prefix

### 10.2 Known Limitations to Document

- Credit score algorithm assumptions
- No authentication/authorization (not required)
- No rate limiting
- Basic error messages (can be improved)
- No pagination on list endpoints

---

## Time Allocation Summary

| Phase | Hours | Priority | uv Impact |
|-------|-------|----------|-----------|
| Infrastructure Setup | 2-3 | Critical | ⚡ -1 hour (faster setup) |
| Data Models | 2-3 | Critical | Same |
| Data Ingestion | 3-4 | Critical | Same |
| Credit Score Engine | 3-4 | Critical | Same |
| API Endpoints | 8-10 | Critical | Same |
| Service Layer | 2 | Critical | Same |
| Testing | 2-3 | Important | Same |
| Docker & Deployment | 2 | Critical | ⚡ Faster builds |
| Documentation | 1-2 | Important | Same |
| **Total** | **25-34** | | **Saved 1-2 hours** |

**Buffer**: 11-15 hours for debugging, breaks, unexpected issues

---

## Key Technical Decisions

### 1. Why uv over pip/poetry?
- **Speed**: 10-100x faster installs (crucial for Docker rebuilds)
- **Simplicity**: No manual venv management
- **Modern**: Uses Rust, actively developed by Astral (ruff creators)
- **Lock file**: Guaranteed reproducible builds
- **Docker-friendly**: Official Docker images, better caching

### 2. Why Celery over Django-Q?
- Industry standard
- Better documentation
- Redis already needed for caching

### 3. Why Pandas over openpyxl alone?
- Robust data cleaning
- Better handling of malformed data
- Easier data type conversion

### 4. Why Service Layer?
- Testability
- Reusability (/check-eligibility and /create-loan share logic)
- Clean separation of concerns

### 5. Why Decimal over Float for money?
- Precision in financial calculations
- No floating-point errors
- Industry best practice

### 6. Database Indexes Strategy
- Index foreign keys (customer in loans)
- Index frequently filtered fields (loan_approved, dates)
- Composite indexes for common query patterns

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Docker issues on submission machine | Test on fresh clone, document clearly |
| Ambiguous credit score algorithm | Document assumptions in README |
| Time overrun | Prioritize critical features, skip bonus |
| Data file format issues | Add robust error handling, validate early |
| Celery not working | Fallback to sync processing if needed |

---

## Success Criteria

✅ **Must Have**:
- All 6 endpoints working
- Docker compose runs successfully
- Data ingestion completes
- Credit score logic implemented
- Clean, organized code

⭐ **Nice to Have**:
- Unit tests
- Comprehensive error messages
- API documentation (Swagger)
- Logging configuration
- Performance optimization

---

## Final Pro Tips

1. **Commit early, commit often** - Shows thought process
2. **Test Docker frequently** - Don't wait until the end
3. **Use git branches** - Feature branches show organization
4. **Document as you go** - Don't leave README for last
5. **Handle errors gracefully** - Better to return error than crash
6. **Keep it simple** - Working simple code > broken complex code
7. **Use meaningful variable names** - Code is read more than written
8. **Add logging** - Helps debug issues during evaluation