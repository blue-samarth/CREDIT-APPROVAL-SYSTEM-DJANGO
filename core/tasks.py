from celery import shared_task
from django.db import OperationalError
import logging

from core.utils.data_ingestion import (
    ingest_customers_from_excel,
    ingest_loans_from_excel
)

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='core.ingest_customer_data',
    autoretry_for=(ConnectionError, IOError, OSError, OperationalError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
)
def ingest_customer_data_task(self, file_path: str) -> dict:
    """Celery task to ingest customer data asynchronously."""
    try:
        logger.info(f"Starting customer data ingestion from {file_path}")
        count = ingest_customers_from_excel(file_path)
        
        result = {
            'status': 'success',
            'customers_created': count,
            'file': file_path,
            'task_id': self.request.id
        }
        
        logger.info(f"Customer ingestion completed: {count} customers created")
        return result
        
    except (ValueError, KeyError) as e:
        logger.error(f"Customer ingestion failed: {e}")
        raise
        
    except Exception as e:
        logger.error(f"Customer ingestion failed: {e}", exc_info=True)
        raise


@shared_task(
    bind=True,
    name='core.ingest_loan_data',
    autoretry_for=(ConnectionError, IOError, OSError, OperationalError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
)
def ingest_loan_data_task(self, file_path, previous_result=None):  # Accept but ignore
    """
    Celery task to ingest loan data.
    
    Args:
        file_path: Path to loan Excel file
        previous_result: Result from previous task in chain (ignored)
    """
    try:
        logger.info(f"Starting loan data ingestion from {file_path}")
        count = ingest_loans_from_excel(file_path)
        
        result = {
            'status': 'success',
            'loans_created': count,
            'file': file_path,
            'task_id': self.request.id
        }
        
        logger.info(f"Loan ingestion completed: {count} loans created")
        return result
        
    except ValueError as e:
        logger.error(f"Loan ingestion failed: {e}")
        raise
        
    except Exception as e:
        logger.error(f"Loan ingestion failed: {e}", exc_info=True)
        raise


@shared_task(
    bind=True,
    name='core.ingest_all_data',
    autoretry_for=(ConnectionError, IOError, OSError, OperationalError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
)
def ingest_all_data_task(self, customers_file: str, loans_file: str) -> dict:
    """Single task to ingest both customers and loans."""
    try:
        logger.info("Starting combined data ingestion")
        
        customers_count = ingest_customers_from_excel(customers_file)
        logger.info(f"Customers ingested: {customers_count}")
        
        loans_count = ingest_loans_from_excel(loans_file)
        logger.info(f"Loans ingested: {loans_count}")
        
        result = {
            'status': 'success',
            'customers_created': customers_count,
            'loans_created': loans_count,
            'task_id': self.request.id
        }
        
        logger.info("Combined data ingestion completed")
        return result
        
    except Exception as e:
        logger.error(f"Combined ingestion failed: {e}", exc_info=True)
        raise