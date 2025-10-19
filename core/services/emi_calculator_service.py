
from decimal import Decimal

class EMICalculatorService:
    """
    EMI calculation using reducing balance method (compound interest).
    
    Formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        
        Where:
        P = Principal (loan amount)
        r = Monthly interest rate (annual_rate / 12 / 100)
        n = Tenure in months    
    """

    @staticmethod
    def calculate_emi(loan_amount: Decimal, annual_interest_rate: Decimal, tenure_months: int) -> Decimal:
        """
        Calculate the EMI for a loan.

        Args:
            loan_amount: Principal loan amount
            annual_interest_rate: Annual interest rate in percentage
            tenure_months: Loan tenure in months

        Returns:
            Calculated EMI rounded to 2 decimal places

        Raises:
            ValueError: If principal <= 0 or tenure_months <= 0
        """
        if loan_amount <= 0:
            raise ValueError("Loan amount must be greater than 0")
        if tenure_months <= 0:
            raise ValueError("Tenure must be greater than 0 months")

        monthly_interest_rate: Decimal = (annual_interest_rate / Decimal('100')) / Decimal('12')

        if monthly_interest_rate == 0:
            emi: Decimal = loan_amount / Decimal(tenure_months)
        else:
            emi: Decimal = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** tenure_months) / ((1 + monthly_interest_rate) ** tenure_months - 1)

        return emi.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_total_interest(emi: Decimal, tenure_months: int, loan_amount: Decimal) -> Decimal:
        """
        Calculate the total interest payable over the loan tenure.

        Args:
            emi: Monthly EMI amount
            tenure_months: Loan tenure in months
            loan_amount: Principal loan amount

        Returns:
            Total interest payable rounded to 2 decimal places
        """
        total_payment: Decimal = emi * Decimal(tenure_months)
        total_interest: Decimal = total_payment - loan_amount
        return total_interest.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_total_payment(emi: Decimal, tenure_months: int) -> Decimal:
        """
        Calculate the total payment over the loan tenure.

        Args:
            emi: Monthly EMI amount
            tenure_months: Loan tenure in months

        Returns:
            Total payment rounded to 2 decimal places
        """
        total_payment: Decimal = emi * Decimal(tenure_months)
        return total_payment.quantize(Decimal('0.01'))
