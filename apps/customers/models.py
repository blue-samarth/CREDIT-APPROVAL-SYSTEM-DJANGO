from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """
    Customer model for storing customer information.
    """
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    phone_number = models.CharField(max_length=15, unique=True, null=False, db_index=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=False, validators=[MinValueValidator(Decimal('0.00'))])
    approved_credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=False, validators=[MinValueValidator(Decimal('0.00'))])
    current_debt = models.DecimalField(max_digits=15, decimal_places=2, null=False, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "customers"
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} (ID: {self.customer_id})"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def calculate_approved_credit_limit(self) -> Decimal:
        """
        Calculate the approved credit limit based on monthly income and age.
        """
        if self.age < 25:
            return self.monthly_income * Decimal('12')
        elif 25 <= self.age < 40:
            return self.monthly_income * Decimal('24')
        elif 40 <= self.age < 60:
            return self.monthly_income * Decimal('36')
        else:
            return self.monthly_income * Decimal('24')
        
    def update_current_debt(self, amount: Decimal, operation: str = 'add') -> None:
        """
        Update the current debt.
        
        Args:
            amount: The amount to add or subtract
            operation: 'add' or 'subtract'
        """
        if amount < 0:
            raise ValueError("Amount must be positive.")
        
        if operation == 'add':
            self.current_debt += amount
        elif operation == 'subtract':
            self.current_debt = max(self.current_debt - amount, Decimal('0.00'))
        else:
            raise ValueError("Operation must be 'add' or 'subtract'")
        
        self.save()

    def soft_delete(self):
        """
        Soft delete the customer by setting is_active to False and recording the deletion time.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()