import os
import pandas as pd

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.customers.models import Customer
from apps.loans.models import Loan


class Command(BaseCommand):
    help: str = "Ingests customer and/or loan data from Excel files into the database."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--customers',
            type=str,
            default="data/customer_data.xlsx",
            help='Path to the Excel file containing customer data.'
        )
        parser.add_argument(
            '--loans',
            type=str,
            default="data/loan_data.xlsx",
            help='Path to the Excel file containing loan data.'
        )

    def handle(self, *args, **options) -> None:
        customers_file: str = options['customers']
        loans_file: str = options['loans']

        if not os.path.exists(customers_file):
            self.stderr.write(self.style.ERROR(f"Customers file not found: {customers_file}"))
            return
        if not os.path.exists(loans_file):
            self.stderr.write(self.style.ERROR(f"Loans file not found: {loans_file}"))
            return

        self.stdout.write(self.style.SUCCESS("Starting data ingestion..."))

        try:
            customer_df = pd.read_excel(customers_file)
            loan_df = pd.read_excel(loans_file)

            customer_df.columns = [col.strip().lower().replace(" ", "_") for col in customer_df.columns]
            loan_df.columns = [col.strip().lower().replace(" ", "_") for col in loan_df.columns]

            customer_df = customer_df.rename(columns={
                "monthly_salary": "monthly_income",
                "approved_limit": "approved_credit_limit"
            })
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading Excel files: {e}"))
            return

        customers_created = 0
        loans_created = 0

        with transaction.atomic():
            for _, row in customer_df.iterrows():
                try:
                    customer, created = Customer.objects.get_or_create(
                        phone_number=row['phone_number'],
                        defaults={
                            "first_name": row['first_name'].strip(),
                            "last_name": row['last_name'].strip(),
                            "age": int(row['age']),
                            "monthly_income": Decimal(row['monthly_income']),
                            "approved_credit_limit": Decimal(row['approved_credit_limit']),
                            "current_debt": Decimal('0.00'),
                            "is_active": True
                        }
                    )
                    if created:
                        customers_created += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error creating customer {row.get('phone_number', '')}: {e}"))

        # --- Loan ingestion ---
        with transaction.atomic():
            for _, row in loan_df.iterrows():
                try:
                    customer = Customer.objects.get(phone_number=row['phone_number'])
                    loan, created = Loan.objects.get_or_create(
                        loan_id=row['loan_id'],
                        defaults={
                            'customer': customer,
                            'loan_amount': row['loan_amount'],
                            'interest_rate': row['interest_rate'],
                            'term_months': row['term_months'],
                            'monthly_payment': row['monthly_payment'],
                            'monthly_payment_due_date': row['monthly_payment_due_date'],
                            'loan_approved': row.get('loan_approved', False),
                            'end_date': row['end_date'],
                            'monthly_payments_made_on_time': row.get('monthly_payments_made_on_time', 0),
                            'is_active': row.get('is_active', True),
                        }
                    )
                    if created:
                        loans_created += 1
                except Customer.DoesNotExist:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Customer with phone number {row.get('phone_number', '')} not found. Skipping loan entry."
                        )
                    )
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f"Error creating loan for customer {row.get('phone_number', '')}: {e}")
                    )

        self.stdout.write(self.style.SUCCESS(f"Customers created: {customers_created}"))
        self.stdout.write(self.style.SUCCESS(f"Loans created: {loans_created}"))
        self.stdout.write(self.style.SUCCESS("Data ingestion completed successfully."))
