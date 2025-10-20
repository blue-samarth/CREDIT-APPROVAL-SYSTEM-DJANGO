from rest_framework import serializers
from apps.customers.models import Customer
from decimal import Decimal

class CustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    age = serializers.IntegerField(min_value=18, max_value=100)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if Customer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return value
    
    def create(self, validated_data: dict) -> Customer:
        customer = Customer.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            monthly_income=validated_data['monthly_income'],
            phone_number=validated_data['phone_number'],
            approved_credit_limit=Decimal('0.00'),
        )
        customer.approved_credit_limit = customer.calculate_approved_credit_limit()
        customer.save()
        return customer
    
class CustomerResponseSerializer(serializers.ModelSerializer):
    customer_id: int = serializers.IntegerField(source='pk', read_only=True)
    monthly_income: Decimal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    approved_credit_limit: Decimal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id',
            'first_name',
            'last_name',
            'age',
            'monthly_income',
            'phone_number',
            'approved_credit_limit',
            'current_debt',
            'is_active',
            'created_at',
            'updated_at'
        ]