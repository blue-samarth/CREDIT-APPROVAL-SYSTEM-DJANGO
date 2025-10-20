from decimal import Decimal

from django.db.models import Sum
from django.db.models.query import QuerySet
from django.utils import timezone

from apps.customers.models import Customer
from apps.loans.models import Loan

class CreditScoreService:
    """
    Calculate customer credit score based on loan history.
    
    Scoring Components (Total: 100 points):
    1. Payment History (30 points) - EMIs paid on time
    2. Number of Loans (20 points) - Fewer loans = better
    3. Current Year Activity (20 points) - Recent loan behavior
    4. Loan Volume (30 points) - Total borrowed vs approved limit
    
    Override Rules:
    - If sum(current_loans) > approved_limit: score = 0
    - If sum(active_EMIs) > 50% of monthly_salary: REJECT
    """
    
    @staticmethod
    def _get_active_loans(customer: Customer) -> 'QuerySet[Loan]':
        """
        Helper method to get active loans for a customer.
        """
        return Loan.objects.filter(
            customer_id=customer,
            is_active=True,
            loan_approved=True
        )
    
    @staticmethod
    def _calculate_payment_history_score(loans: QuerySet) -> Decimal:
        """
        Component 1: Payment History (30 points)
        
        Formula:
            score = (total_emis_paid_on_time / total_emis) * 30
        
        Args:
            loans: QuerySet of all customer loans (active + completed)
        
        Returns:
            Score (0-30)
        """
        if not loans.exists(): return Decimal('0')

        total_emis_expected: int = loans.aggregate(total=Sum('term_months'))['total'] or 1
        total_emis_paid: int = loans.aggregate(total=Sum('monthly_payments_made_on_time'))['total'] or 0

        payment_history_ratio: Decimal = Decimal(total_emis_paid) / Decimal(max(total_emis_expected, 1))
        return payment_history_ratio * Decimal('30')
    
    @staticmethod
    def _calculate_loan_count_score(loans: QuerySet) -> int:
        """
        Component 2: Number of Loans (20 points)
        
        Scoring:
            0-2 loans: 20 points (excellent)
            3-4 loans: 15 points (good)
            5-6 loans: 10 points (moderate)
            7+ loans:   5 points (risky)
        Args:
            loans: QuerySet of active loans
        Returns:
            Score (0-20)
        """

        num_loans: int = loans.count()
        if num_loans <= 2:
            return 20
        elif num_loans in [3, 4]:
            return 15
        elif num_loans in [5, 6]:
            return 10
        else:
            return 5
        
    @staticmethod
    def _calculate_current_year_activity_score(loans: QuerySet) -> int:
        """
        Component 3: Current Year Activity (20 points)
        
        Scoring:
            0 loans this year: 20 points (excellent)
            1-2 loans:         15 points (good)
            3-4 loans:         10 points (moderate)
            5+ loans:           5 points (risky)
        
        Args:
            loans: QuerySet of active loans
        Returns:
            Score (0-20)
        """
        current_year = timezone.now().year
        recent_loans_count: int = loans.filter(start_date__year=current_year).count()

        if recent_loans_count == 0:
            return 5
        elif recent_loans_count <= 2:
            return 20
        elif recent_loans_count <= 4:
            return 15
        else:
            return 5
        
    @staticmethod
    def _calculate_loan_volume_score(customer: Customer, loans: QuerySet) -> int:
        """
        Component 4: Loan Volume (30 points)
        
        Scoring:
            <=30% of approved limit: 30 points (excellent)
            31%-60% of approved limit: 20 points (good)
            61%-90% of approved limit: 10 points (moderate)
            >90% of approved limit:    5 points (risky)
        
        Args:
            customer: Customer instance
            loans: QuerySet of active loans
        Returns:
            Score (0-30)
        """
        approved_limit: Decimal = customer.approved_credit_limit
        total_current_loans: Decimal = loans.aggregate(total=Sum('loan_amount'))['total'] or Decimal('0.00')

        if approved_limit <= 0:
            return 0

        loan_volume_ratio: Decimal = total_current_loans / approved_limit

        if loan_volume_ratio <= Decimal('0.5'):
            return 30
        elif loan_volume_ratio <= Decimal('1.0'):
            return 25
        elif loan_volume_ratio <= Decimal('1.5'):
            return 15
        else:
            return 5
        
    @staticmethod
    def _check_approved_limit_override(customer: Customer, active_loans: QuerySet) -> bool:
        """
        Check if the customer's approved limit should be overridden based on their current loan status.

        Args:
            customer: Customer instance
            active_loans: QuerySet of active loans

        Returns:
            bool: True if the approved limit should be overridden, False otherwise
        """
        if not active_loans.exists():
            return False

        # Check if the total loan amount exceeds the approved limit
        total_loan_amount: Decimal = active_loans.aggregate(total=Sum('loan_amount'))['total'] or Decimal('0.00')
        return total_loan_amount > customer.approved_credit_limit
    

    @classmethod
    def calculate_credit_score(cls, customer: Customer) -> dict:
        """
        Calculate the credit score for a customer.

        Args:
            customer: Customer instance

        Returns:
            dict: {
                'score': Decimal (0-100),
                'approval': bool (True if approved, False if rejected)
            }
        """
        active_loans = cls._get_active_loans(customer)
        all_loans = Loan.objects.filter(customer_id=customer)

        if cls._check_approved_limit_override(customer, active_loans): return {'score': Decimal('0'), 'approval': False}

        payment_history_score = cls._calculate_payment_history_score(all_loans)
        loan_count_score = cls._calculate_loan_count_score(active_loans)
        current_year_activity_score = cls._calculate_current_year_activity_score(active_loans)
        loan_volume_score = cls._calculate_loan_volume_score(customer, active_loans)

        total_score: Decimal = (
            payment_history_score +
            Decimal(loan_count_score) +
            Decimal(current_year_activity_score) +
            Decimal(loan_volume_score)
        )

        approval: bool = total_score >= Decimal('50')

        return {
            'score': total_score,
            'approval': approval
        }