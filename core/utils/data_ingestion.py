import os
import pandas as pd
from decimal import Decimal

from django.db import transaction
from apps.customers.models import Customer
from apps.loans.models import Loan


def ingest_customers_from_excel(file_path: str) -> int:
    """
    Ingest customer data from an Excel file.

    Args:
        file_path: Path to the customer Excel file

    Returns:
        Number of customers created (excludes duplicates)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Customer file not found: {file_path}")

    customer_df = pd.read_excel(file_path)
    customer_df.columns = [col.strip().lower().replace(" ", "_") for col in customer_df.columns]
    
    customer_df = customer_df.rename(columns={
        "monthly_salary": "monthly_income",
        "approved_limit": "approved_credit_limit"
    })

    customers_created = 0

    with transaction.atomic():
        for _, row in customer_df.iterrows():
            try:
                customer, created = Customer.objects.get_or_create(
                    customer_id=row['customer_id'],
                    defaults={
                        "phone_number": row['phone_number'],
                        "first_name": row['first_name'].strip(),
                        "last_name": row['last_name'].strip(),
                        "age": int(row['age']),
                        "monthly_income": Decimal(str(row['monthly_income'])),
                        "approved_credit_limit": Decimal(str(row['approved_credit_limit'])),
                        "current_debt": Decimal('0.00'),
                        "is_active": True
                    }
                )
                if created:
                    customers_created += 1
            except Exception as e:
                raise ValueError(f"Error processing customer {row.get('customer_id', 'unknown')}: {e}")

    return customers_created


def ingest_loans_from_excel(file_path: str) -> int:
    """
    Ingest loan data from an Excel file.

    Args:
        file_path: Path to the loan Excel file

    Returns:
        Number of loans created (excludes duplicates)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Loan file not found: {file_path}")

    loan_df = pd.read_excel(file_path)
    loan_df.columns = [col.strip().lower().replace(" ", "_") for col in loan_df.columns]
    
    loan_df = loan_df.rename(columns={
        "tenure": "term_months",
        "emis_paid_on_time": "monthly_payments_made_on_time",
        "date_of_approval": "loan_approved_date"
    })

    loans_created = 0

    with transaction.atomic():
        for _, row in loan_df.iterrows():
            try:
                if 'customer_id' not in row or pd.isna(row['customer_id']):
                    continue
                
                customer = Customer.objects.get(customer_id=int(row['customer_id']))
                
                loan_approved = False
                if 'loan_approved_date' in row and pd.notna(row['loan_approved_date']):
                    loan_approved = True
                
                loan, created = Loan.objects.get_or_create(
                    loan_id=row['loan_id'],
                    defaults={
                        'customer_id': customer,
                        'loan_amount': Decimal(str(row['loan_amount'])),
                        'interest_rate': Decimal(str(row['interest_rate'])),
                        'term_months': int(row['term_months']),
                        'monthly_payment': Decimal(str(row.get('monthly_payment', 0))),
                        'monthly_payment_due_date': int(row.get('monthly_payment_due_date', 1)),
                        'loan_approved': loan_approved,
                        'end_date': pd.to_datetime(row['end_date']),
                        'monthly_payments_made_on_time': int(row.get('monthly_payments_made_on_time', 0)),
                        'is_active': bool(row.get('is_active', True)),
                    }
                )
                if created:
                    loans_created += 1
                    
            except Customer.DoesNotExist:
                continue
            except Exception as e:
                raise ValueError(f"Error processing loan {row.get('loan_id', 'unknown')}: {e}")

    return loans_created