from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.customers.models import Customer

class Loan(models.Model):
    """
    Loan model for storing loan information.
    """
    loan_id: str = models.AutoField(primary_key=True)
    customer_id: Customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='loans', db_index=True)
    loan_amount: Decimal = models.DecimalField(max_digits=15, decimal_places=2, null=False, validators=[MinValueValidator(Decimal('100.00'))])
    interest_rate: Decimal = models.DecimalField(max_digits=5, decimal_places=2, null=False, validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))])
    term_months: int = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(360)])
    monthly_payment: Decimal = models.DecimalField(max_digits=15, decimal_places=2, null=False, validators=[MinValueValidator(Decimal('0.00'))], help_text="EMI amount to be paid")
    monthly_payments_made_on_time: int = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], help_text="Count of EMIs paid on time for credit score")
    monthly_payment_due_date: int = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(28)], help_text="Day of the month when payment is due")
    loan_approved: bool = models.BooleanField(default=False, db_index=True)
    start_date: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    end_date: models.DateTimeField = models.DateTimeField()
    is_active: bool = models.BooleanField(default=True, db_index=True)
    deleted_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loans"
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['customer_id', 'loan_approved'])
        ]

    def __str__(self) -> str:
        return f"Loan ID: {self.loan_id} for Customer ID: {self.customer_id.customer_id}"
    
    @property
    def repayments_left(self) -> int:
        """
        Calculate the number of repayments left.
        """
        total_payments = self.term_months
        payments_made = self.monthly_payments_made_on_time
        return max(total_payments - payments_made, 0)
    
    @property
    def is_active_loan(self) -> bool:
        """
        Check if the loan is still active based on end date and is_active flag.
        """
        return self.is_active and timezone.now() < self.end_date
    
    def calculate_monthly_payment(self) -> Decimal:
        """
        Calculate the monthly payment (EMI) using the formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
        P = loan amount
        r = monthly interest rate
        n = number of monthly payments
        """
        P = self.loan_amount
        r = (self.interest_rate / Decimal('100')) / Decimal('12')
        n = self.term_months
        
        if r == 0:
            return P / n
        
        emi = P * r * (1 + r) ** n / ((1 + r) ** n - 1)
        return emi.quantize(Decimal('0.01'))
    
    def calculate_total_interest(self) -> Decimal:
        """
        Calculate the total interest payable over the term of the loan.
        Total Interest = (EMI * n) - P
        """
        emi = self.calculate_monthly_payment()
        total_payment = emi * self.term_months
        total_interest = total_payment - self.loan_amount
        return total_interest.quantize(Decimal('0.01'))
    
    def soft_delete(self) -> None:
        """
        Soft delete the loan by setting is_active to False and recording deleted_at timestamp.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()
    
    def save(self, *args, **kwargs):
        """Calculate end_date and monthly_payment if not provided"""
        if not self.end_date and self.start_date:
            self.end_date = self.start_date + timedelta(days=30 * self.term_months)
        if self.monthly_payment == 0 or not self.monthly_payment:
            self.monthly_payment = self.calculate_monthly_payment()
        super().save(*args, **kwargs)