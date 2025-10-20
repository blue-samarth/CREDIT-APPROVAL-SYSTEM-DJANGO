from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from apps.loans.models import Loan
from apps.customers.models import Customer
from core.services.loan_eligibility_service import LoanEligibilityService

class LoanCreationService:
    """
    Service to create loans for eligible customers.
    
    Steps:
    1. Check loan eligibility using LoanEligibilityService.
    2. If eligible, create Loan record with calculated EMI and tenure dates.
    3. Return loan creation status and details.
    """

    @staticmethod
    @transaction.atomic
    def create_loan(customer_id: int, loan_amount: Decimal, interest_rate: Decimal, term_months: int) -> dict[str, any]:
        """
        Create a loan for an eligible customer.
        
        Args:
            customer_id: ID of the customer applying for the loan
            loan_amount: Requested loan amount
            interest_rate: Interest rate for the loan
            term_months: Loan tenure in months
        
        Returns:
            dict with keys:
                - 'success': bool indicating if loan was created
                - 'loan': Loan instance if created, else None
                - 'message': str with details
        """
        eligibility_response = LoanEligibilityService.check_eligibility(
            customer_id=customer_id,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            tenure_months=term_months
        )

        if not eligibility_response['approval']:
            return {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': eligibility_response.get('message', 'Loan not approved based on credit evaluation'),
                'monthly_installment': Decimal('0.00')
            }

        try:
            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(pk=customer_id)
                today: timezone.datetime = timezone.now()
                end_date: timezone.datetime = today + relativedelta(months=term_months)

                loan: Loan = Loan.objects.create(
                    customer_id=customer,
                    loan_amount=loan_amount,
                    interest_rate=eligibility_response['corrected_interest_rate'],
                    term_months=term_months,
                    monthly_installment=eligibility_response['monthly_installment'],
                    monthly_payment_due_date=5,
                    start_date=today,
                    end_date=end_date,
                    is_active=True,
                    loan_approved=True
                )

                customer.current_debt += loan_amount
                customer.save()
                return {
                    'loan_id': loan.loan_id,
                    'customer_id': customer_id,
                    'loan_amount': loan.loan_amount,
                    'interest_rate': loan.interest_rate,
                    'term_months': loan.term_months,
                    'loan_approved': True,
                    'message': 'Loan successfully created',
                    'monthly_installment': loan.monthly_payment
                }
        except Customer.DoesNotExist:
            return {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': 'Customer does not exist',
                'monthly_installment': Decimal('0.00')
            }
