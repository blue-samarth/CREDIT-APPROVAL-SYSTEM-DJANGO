from rest_framework import serializers
from decimal import Decimal

from .models import Loan
from apps.customers.models import Customer

class CustomerBasicSerializer(serializers.ModelSerializer):
    id: int = serializers.IntegerField(source='customer_id')
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number']

class LoanDetailSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(read_only=True)
    customer_id = serializers.IntegerField(source='customer.customer_id', read_only=True)
    loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    term_months = serializers.IntegerField()

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer_id',
            'loan_amount',
            'term_months',
            'interest_rate',
            'monthly_payment',
        ]

class LoanCreateSerializer(serializers.ModelSerializer):
    loan_id: int = serializers.IntegerField(source='pk', read_only=True)
    repayments_left: int = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'loan_amount',
            'interest_rate',
            'term_months',
            'monthly_payment_due_date',
        ]

class LoanEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    term_months = serializers.IntegerField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value, is_active=True).exists():
            raise serializers.ValidationError("Active customer with given ID does not exist.")
        return value
    
class LoanEligibilityResponseSerializer(serializers.Serializer):
    customer_id: int = serializers.IntegerField()
    approval: bool = serializers.BooleanField()
    interest_rate: Decimal = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure: int = serializers.IntegerField()
    corrected_interest_rate: Decimal = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment: Decimal = serializers.DecimalField(max_digits=15, decimal_places=2)
    tenure_months: int = serializers.IntegerField()


class LoanCreationRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    term_months = serializers.IntegerField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    def validate_customer_id(self, value):
        try:
            customer = Customer.objects.get(customer_id=value, is_active=True)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Active customer with given ID does not exist.")
        return value
    
class LoanCreationResponseSerializer(serializers.Serializer):
    loan_id: int = serializers.IntegerField(allow_null=True, required=False)
    customer_id: int = serializers.IntegerField()
    loan_approved: bool = serializers.BooleanField()
    message: str = serializers.CharField()
    interest_rate: Decimal = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    term_months: int = serializers.IntegerField(required=False)
    monthly_installment = serializers.DecimalField(max_digits=15, decimal_places=2)
