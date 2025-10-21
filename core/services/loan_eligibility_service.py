from decimal import Decimal
from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Sum

from apps.customers.models import Customer
from apps.loans.models import Loan
from core.services.credit_score_service import CreditScoreService
from core.services.emi_calculator_service import EMICalculatorService

class LoanEligibilityService:
    """
    Determine loan eligibility for customers.
    
    Checks:
    1. Credit score calculation
    2. Interest rate correction based on score bands
    3. EMI constraint (monthly EMIs <= 50% of salary)
    4. Approved limit check
    
    Returns comprehensive eligibility response for API endpoints.
    """

    @staticmethod
    def _apply_interest_correction(credit_score: int, requested_rate: Decimal) -> tuple[bool, Decimal, str]:
        """
        Apply interest rate correction based on credit score.
        
        Credit Score Bands (from plan.md):
            Score > 50:        Approve at any rate
            50 >= Score > 30:  Approve, minimum 12%
            30 >= Score > 10:  Approve, minimum 16%
            Score <= 10:       Reject
        
        Args:
            credit_score: Customer's credit score (0-100)
            requested_rate: Requested interest rate
        
        Returns:
            (approval, corrected_rate, message)
            - approval: bool - Whether loan is approved
            - corrected_rate: Decimal - Adjusted interest rate
            - message: str - Approval/rejection reason
        """
        if credit_score > 50:
            return True, requested_rate, "Approved at requested rate."
        elif 30 < credit_score <= 50:
            min_rate = Decimal('12.00')
            if requested_rate < min_rate:
                return True, min_rate, f"Approved with interest rate adjusted to {min_rate}% due to credit score."
            return True, requested_rate, "Approved at requested rate."
        elif 10 < credit_score <= 30:
            min_rate = Decimal('16.00')
            if requested_rate < min_rate:
                return True, min_rate, f"Approved with interest rate adjusted to {min_rate}% due to credit score."
            return True, requested_rate, "Approved at requested rate."
        else:
            return False, requested_rate, "Rejected due to low credit score."
        
    @staticmethod
    def _check_emi_constraint(customer: Customer, loan_amount: Decimal, interest_rate: Decimal, tenure_months: int) -> tuple[bool, str]:
        """
        Check if the EMI for the requested loan is within the acceptable limit.

        Args:
            customer: Customer instance
            loan_amount: Requested loan amount
            interest_rate: Approved interest rate
            tenure_months: Loan tenure in months

        Returns:
            (is_within_limit, message)
        """
        new_emi: Decimal = EMICalculatorService.calculate_emi(loan_amount=loan_amount, annual_interest_rate=interest_rate, tenure_months=tenure_months)

        active_loans: QuerySet[Loan] = CreditScoreService._get_active_loans(customer)
        existing_emis = active_loans.aggregate(total=Sum('monthly_payment'))['total'] or Decimal('0')

        total_emis: Decimal = existing_emis + new_emi

        max_allowed: Decimal = customer.monthly_income * Decimal('0.5')

        if total_emis > max_allowed:
            return False, f"EMI burden ({total_emis}) exceeds 50% of monthly income"
        else:
            return True, "Approved"
        
    @classmethod
    def check_eligibility(cls, customer_id: int, loan_amount: Decimal, interest_rate: Decimal, tenure_months: int) -> dict[str, Any]:
        """
        Check if customer is eligible for a loan.
        
        Args:
            customer_id: Customer ID
            loan_amount: Requested loan amount
            interest_rate: Requested annual interest rate
            tenure_months: Requested tenure in months
        
        Returns:
            Dictionary with:
            {
                'approval': bool,
                'customer_id': int,
                'credit_score': int,
                'interest_rate': Decimal,  # Original requested
                'corrected_interest_rate': Decimal,  # After correction
                'monthly_installment': Decimal,
                'message': str,  # Approval or rejection reason
                'tenure_months': int
            }
        
        Raises:
            Customer.DoesNotExist: If customer not found        
        """

        customer: Customer = Customer.objects.get(customer_id=customer_id)

        credit_score_result: dict[str, Any] = CreditScoreService.calculate_credit_score(customer)
        credit_score: int = int(credit_score_result['score'])

        approval, corrected_rate, rate_message = cls._apply_interest_correction(credit_score, interest_rate)

        if not approval:
            return {
                'approval': False,
                'customer_id': customer_id,
                'credit_score': credit_score,
                'interest_rate': interest_rate,
                'corrected_interest_rate': corrected_rate,
                'monthly_payment': Decimal('0.00'),
                'message': rate_message,
                'tenure_months': tenure_months
            }

        emi_approval, emi_message = cls._check_emi_constraint(customer, loan_amount, corrected_rate, tenure_months)

        if not emi_approval:
            return {
                'approval': False,
                'customer_id': customer_id,
                'credit_score': credit_score,
                'interest_rate': interest_rate,
                'corrected_interest_rate': corrected_rate,
                'monthly_payment': Decimal('0.00'),
                'message': emi_message,
                'tenure_months': tenure_months
            }

        monthly_installment: Decimal = EMICalculatorService.calculate_emi(loan_amount, corrected_rate, tenure_months)

        return {
            'approval': True,
            'customer_id': customer_id,
            'credit_score': credit_score,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_rate,
            'monthly_payment': monthly_installment,
            'message': "Loan approved.",
            'tenure_months': tenure_months
        }
    
