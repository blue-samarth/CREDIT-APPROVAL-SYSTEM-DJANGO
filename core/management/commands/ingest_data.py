import os
from django.core.management.base import BaseCommand
from celery import chain
from core.tasks import ingest_customer_data_task, ingest_loan_data_task


class Command(BaseCommand):
    help: str = "Ingests customer and loan data asynchronously via Celery."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--customers',
            type=str,
            default="data/customer_data.xlsx",
            help='Path to customer data Excel file.'
        )
        parser.add_argument(
            '--loans',
            type=str,
            default="data/loan_data.xlsx",
            help='Path to loan data Excel file.'
        )

    def handle(self, *args, **options) -> None:
        customers_file = options['customers']
        loans_file = options['loans']

        # Validate files exist
        if not os.path.exists(customers_file):
            self.stderr.write(self.style.ERROR(f"❌ File not found: {customers_file}"))
            return
        
        if not os.path.exists(loans_file):
            self.stderr.write(self.style.ERROR(f"❌ File not found: {loans_file}"))
            return

        # Create Celery chain (customers → loans)
        workflow = chain(
            ingest_customer_data_task.s(customers_file),
            ingest_loan_data_task.si(loans_file)
        )

        # Execute asynchronously
        result = workflow.apply_async()

        # Output
        self.stdout.write(self.style.SUCCESS("✓ Data ingestion started"))
        self.stdout.write(self.style.SUCCESS(f"  Task ID: {result.id}"))
        self.stdout.write(self.style.SUCCESS(f"  Monitor: http://localhost:5555"))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("     Make sure Celery worker is running:"))
        self.stdout.write(self.style.WARNING("     uv run celery -A config worker --loglevel=info"))