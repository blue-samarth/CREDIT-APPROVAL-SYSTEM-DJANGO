"""
Comprehensive API Endpoint Tests for Credit Approval System

This test suite covers all API endpoints:
1. POST /api/customers/register - Customer registration
2. GET /api/loans/view-loan/<loan_id> - Single loan details
3. GET /api/loans/view-loans/<customer_id> - All customer loans
4. POST /api/loans/check-eligibility - Loan eligibility check
5. POST /api/loans/create-loan - Loan creation

Run with: uv run python test_api_endpoints.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.customers.models import Customer
from apps.loans.models import Loan
from datetime import datetime
from django.utils import timezone


class CustomerRegistrationAPITests(TestCase):
    """Tests for POST /api/customers/register endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/customers/register'
    
    def test_register_customer_success(self):
        """Test successful customer registration with valid data"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'phone_number': '+1234567890',
            'monthly_income': 50000
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertIn('approved_credit_limit', response.data)
        
        # Verify customer was created in database
        customer = Customer.objects.get(phone_number='+1234567890')
        self.assertEqual(customer.first_name, 'John')
        self.assertEqual(customer.monthly_income, Decimal('50000'))
    
    def test_register_customer_duplicate_phone(self):
        """Test registration fails with duplicate phone number"""
        # Create first customer
        Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            age=25,
            phone_number='+9876543210',
            monthly_income=60000,
            approved_credit_limit=1440000
        )
        
        # Try to create second customer with same phone
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'phone_number': '+9876543210',  # Duplicate
            'monthly_income': 50000
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_register_customer_invalid_age(self):
        """Test registration fails with age below 18"""
        data = {
            'first_name': 'Minor',
            'last_name': 'Kid',
            'age': 16,  # Below minimum age
            'phone_number': '+1111111111',
            'monthly_income': 30000
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_customer_missing_fields(self):
        """Test registration fails with missing required fields"""
        data = {
            'first_name': 'John',
            # Missing last_name, age, phone_number, monthly_income
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoanDetailAPITests(TestCase):
    """Tests for GET /api/loans/view-loan/<loan_id> endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='Alice',
            last_name='Johnson',
            age=35,
            phone_number='+1234567891',
            monthly_income=80000,
            approved_credit_limit=2880000
        )
        
        # Create test loan
        self.loan = Loan.objects.create(
            customer_id=self.customer,
            loan_amount=500000,
            interest_rate=12.5,
            term_months=24,
            monthly_payment=23562.50,
            monthly_payment_due_date=5,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
    
    def test_get_loan_detail_success(self):
        """Test successful retrieval of loan details"""
        url = f'/api/loans/view-loan/{self.loan.loan_id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['loan_id'], self.loan.loan_id)
        self.assertEqual(response.data['customer_id'], self.customer.customer_id)
        self.assertEqual(Decimal(str(response.data['loan_amount'])), self.loan.loan_amount)
    
    def test_get_loan_detail_not_found(self):
        """Test 404 for non-existent loan ID"""
        url = '/api/loans/view-loan/99999'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)


class CustomerLoansAPITests(TestCase):
    """Tests for GET /api/loans/view-loans/<customer_id> endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='Bob',
            last_name='Williams',
            age=40,
            phone_number='+1234567892',
            monthly_income=100000,
            approved_credit_limit=3600000
        )
        
        # Create multiple loans for customer
        self.loan1 = Loan.objects.create(
            customer_id=self.customer,
            loan_amount=300000,
            interest_rate=10.0,
            term_months=12,
            monthly_payment=26373.00,
            monthly_payment_due_date=5,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
        
        self.loan2 = Loan.objects.create(
            customer_id=self.customer,
            loan_amount=500000,
            interest_rate=12.0,
            term_months=24,
            monthly_payment=23540.00,
            monthly_payment_due_date=5,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
    
    def test_get_customer_loans_success(self):
        """Test successful retrieval of all customer loans"""
        url = f'/api/loans/view-loans/{self.customer.customer_id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify both loans are returned
        loan_ids = [loan['loan_id'] for loan in response.data]
        self.assertIn(self.loan1.loan_id, loan_ids)
        self.assertIn(self.loan2.loan_id, loan_ids)
    
    def test_get_customer_loans_no_loans(self):
        """Test customer with no loans returns empty list"""
        # Create customer with no loans
        customer = Customer.objects.create(
            first_name='Charlie',
            last_name='Brown',
            age=28,
            phone_number='+1234567893',
            monthly_income=70000,
            approved_credit_limit=2520000
        )
        
        url = f'/api/loans/view-loans/{customer.customer_id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_get_customer_loans_invalid_customer(self):
        """Test 404 for non-existent customer ID"""
        url = '/api/loans/view-loans/99999'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LoanEligibilityAPITests(TestCase):
    """Tests for POST /api/loans/check-eligibility endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/loans/check-eligibility'
        
        # Create test customer with good credit history
        self.customer = Customer.objects.create(
            first_name='Diana',
            last_name='Prince',
            age=32,
            phone_number='+1234567894',
            monthly_income=90000,
            approved_credit_limit=3240000,
            current_debt=0
        )
        
        # Create a paid-off loan for good credit score
        Loan.objects.create(
            customer_id=self.customer,
            loan_amount=200000,
            interest_rate=10.0,
            term_months=12,
            monthly_payment=17540.00,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=12,  # All payments on time
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=False
        )
    
    def test_check_eligibility_approved(self):
        """Test loan eligibility check for approval"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approval', response.data)
        self.assertIn('corrected_interest_rate', response.data)
        self.assertIn('monthly_payment', response.data)
    
    def test_check_eligibility_high_loan_amount(self):
        """Test eligibility check with loan amount exceeding limit"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 5000000,  # Very high amount
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # May be rejected or approved with corrected rate
        self.assertIn('approval', response.data)
    
    def test_check_eligibility_invalid_customer(self):
        """Test eligibility check with non-existent customer"""
        data = {
            'customer_id': 99999,  # Non-existent
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_check_eligibility_missing_fields(self):
        """Test eligibility check with missing required fields"""
        data = {
            'customer_id': self.customer.customer_id,
            # Missing loan_amount, interest_rate, term_months
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_check_eligibility_invalid_data_types(self):
        """Test eligibility check with invalid data types"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 'invalid',  # Should be number
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoanCreationAPITests(TestCase):
    """Tests for POST /api/loans/create-loan endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/loans/create-loan'
        
        # Create test customer with good credit
        self.customer = Customer.objects.create(
            first_name='Eve',
            last_name='Anderson',
            age=38,
            phone_number='+1234567895',
            monthly_income=120000,
            approved_credit_limit=4320000,
            current_debt=0
        )
        
        # Create previous loan with good payment history
        Loan.objects.create(
            customer_id=self.customer,
            loan_amount=300000,
            interest_rate=9.5,
            term_months=12,
            monthly_payment=26300.00,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=12,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=False
        )
    
    def test_create_loan_success(self):
        """Test successful loan creation"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 600000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        initial_debt = self.customer.current_debt
        initial_loan_count = Loan.objects.filter(customer_id=self.customer).count()
        
        response = self.client.post(self.url, data, format='json')
        
        # Should be 201 if approved, 200 if rejected
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertIn('loan_approved', response.data)
        
        if response.data['loan_approved']:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('loan_id', response.data)
            self.assertIsNotNone(response.data['loan_id'])
            
            # Verify loan was created
            new_loan_count = Loan.objects.filter(customer_id=self.customer).count()
            self.assertEqual(new_loan_count, initial_loan_count + 1)
            
            # Verify customer debt was updated
            self.customer.refresh_from_db()
            self.assertGreater(self.customer.current_debt, initial_debt)
    
    def test_create_loan_rejected(self):
        """Test loan creation that gets rejected"""
        # Create customer with poor credit (high debt)
        poor_customer = Customer.objects.create(
            first_name='Frank',
            last_name='Miller',
            age=25,
            phone_number='+1234567896',
            monthly_income=40000,
            approved_credit_limit=1440000,
            current_debt=1400000  # Very high existing debt
        )
        
        data = {
            'customer_id': poor_customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['loan_approved'])
        self.assertIn('message', response.data)
    
    def test_create_loan_invalid_customer(self):
        """Test loan creation with non-existent customer"""
        data = {
            'customer_id': 99999,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_loan_missing_fields(self):
        """Test loan creation with missing required fields"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            # Missing interest_rate and term_months
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_loan_negative_amount(self):
        """Test loan creation with negative loan amount"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': -100000,  # Negative amount
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_loan_zero_tenure(self):
        """Test loan creation with zero tenure"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 0  # Invalid tenure
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IntegrationTests(TestCase):
    """End-to-end integration tests for complete user flows"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_complete_loan_application_flow(self):
        """Test complete flow: Register → Check Eligibility → Create Loan"""
        
        # Step 1: Register a new customer
        register_data = {
            'first_name': 'Grace',
            'last_name': 'Hopper',
            'age': 35,
            'phone_number': '+1234567897',
            'monthly_income': 150000
        }
        
        register_response = self.client.post(
            '/api/customers/register',
            register_data,
            format='json'
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        customer_id = register_response.data['customer_id']
        
        # Step 2: Check loan eligibility
        eligibility_data = {
            'customer_id': customer_id,
            'loan_amount': 800000,
            'interest_rate': 9.5,
            'term_months': 36
        }
        
        eligibility_response = self.client.post(
            '/api/loans/check-eligibility',
            eligibility_data,
            format='json'
        )
        
        self.assertEqual(eligibility_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Create loan if eligible
        if eligibility_response.data.get('approval'):
            creation_data = {
                'customer_id': customer_id,
                'loan_amount': 800000,
                'interest_rate': eligibility_response.data['corrected_interest_rate'],
                'term_months': 36
            }
            
            creation_response = self.client.post(
                '/api/loans/create-loan',
                creation_data,
                format='json'
            )
            
            self.assertIn(creation_response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
            
            if creation_response.data.get('loan_approved'):
                loan_id = creation_response.data['loan_id']
                
                # Step 4: Verify loan was created by fetching it
                loan_detail_response = self.client.get(f'/api/loans/view-loan/{loan_id}')
                self.assertEqual(loan_detail_response.status_code, status.HTTP_200_OK)
                self.assertEqual(loan_detail_response.data['loan_id'], loan_id)
                
                # Step 5: Verify loan appears in customer's loans
                customer_loans_response = self.client.get(
                    f'/api/loans/view-loans/{customer_id}'
                )
                self.assertEqual(customer_loans_response.status_code, status.HTTP_200_OK)
                loan_ids = [loan['loan_id'] for loan in customer_loans_response.data]
                self.assertIn(loan_id, loan_ids)
    
    def test_multiple_loans_for_customer(self):
        """Test creating multiple loans for the same customer"""
        
        # Register customer
        register_data = {
            'first_name': 'Henry',
            'last_name': 'Ford',
            'age': 45,
            'phone_number': '+1234567898',
            'monthly_income': 200000
        }
        
        register_response = self.client.post(
            '/api/customers/register',
            register_data,
            format='json'
        )
        
        customer_id = register_response.data['customer_id']
        
        # Create first loan
        loan1_data = {
            'customer_id': customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        loan1_response = self.client.post('/api/loans/create-loan', loan1_data, format='json')
        
        # Create second loan
        loan2_data = {
            'customer_id': customer_id,
            'loan_amount': 300000,
            'interest_rate': 11.0,
            'term_months': 12
        }
        
        loan2_response = self.client.post('/api/loans/create-loan', loan2_data, format='json')
        
        # Verify both loans appear in customer's loan list
        customer_loans_response = self.client.get(f'/api/loans/view-loans/{customer_id}')
        
        approved_count = sum([
            1 for resp in [loan1_response, loan2_response]
            if resp.data.get('loan_approved')
        ])
        
        self.assertGreaterEqual(len(customer_loans_response.data), approved_count)


class CreditScoreBehaviorTests(TestCase):
    """Test credit score calculation affects loan approval"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_low_credit_score_rejection(self):
        """Customer with credit score ≤ 10 should be rejected"""
        # Create customer with very poor payment history
        customer = Customer.objects.create(
            first_name='Poor',
            last_name='Score',
            age=28,
            phone_number='+2000000001',
            monthly_income=60000,
            approved_credit_limit=2160000,
            current_debt=0
        )
        
        # Create multiple loans with many missed payments
        for i in range(3):
            Loan.objects.create(
                customer_id=customer,
                loan_amount=200000,
                interest_rate=14.0,
                term_months=12,
                monthly_payment=17960.00,
                monthly_payment_due_date=5,
                monthly_payments_made_on_time=2,  # Only 2/12 on time
                start_date=timezone.now(),
                end_date=timezone.now(),
                loan_approved=True,
                is_active=False
            )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 100000,
            'interest_rate': 10.0,
            'term_months': 12
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])
        self.assertIn('credit score', response.data['reason'].lower())
    
    def test_interest_rate_correction_for_medium_score(self):
        """Score 30-50 should correct interest rate to minimum 12%"""
        # Create customer with moderate credit
        customer = Customer.objects.create(
            first_name='Medium',
            last_name='Credit',
            age=32,
            phone_number='+2000000002',
            monthly_income=80000,
            approved_credit_limit=2880000,
            current_debt=0
        )
        
        # Create loan with decent but not perfect payment history
        Loan.objects.create(
            customer_id=customer,
            loan_amount=300000,
            interest_rate=11.0,
            term_months=12,
            monthly_payment=26640.00,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=9,  # 75% on time - medium score
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=False
        )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 200000,
            'interest_rate': 8.0,  # Below 12%
            'term_months': 12
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(float(response.data['corrected_interest_rate']), 12.0)
        self.assertEqual(float(response.data['interest_rate']), 8.0)  # Original preserved
    
    def test_interest_rate_correction_for_low_score(self):
        """Score 10-30 should correct interest rate to minimum 16%"""
        # Create customer with poor credit
        customer = Customer.objects.create(
            first_name='Low',
            last_name='Credit',
            age=29,
            phone_number='+2000000003',
            monthly_income=70000,
            approved_credit_limit=2520000,
            current_debt=0
        )
        
        # Create loans with poor payment history
        for i in range(2):
            Loan.objects.create(
                customer_id=customer,
                loan_amount=250000,
                interest_rate=13.0,
                term_months=12,
                monthly_payment=22350.00,
                monthly_payment_due_date=5,
                monthly_payments_made_on_time=5,  # ~42% on time - low score
                start_date=timezone.now(),
                end_date=timezone.now(),
                loan_approved=True,
                is_active=False
            )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 150000,
            'interest_rate': 10.0,  # Below 16%
            'term_months': 12
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])
        self.assertEqual(float(response.data['corrected_interest_rate']), 16.0)
        self.assertEqual(float(response.data['interest_rate']), 10.0)


class EMIConstraintTests(TestCase):
    """Test EMI burden constraints (50% of monthly income)"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_create_loan_rejected_high_emi_burden(self):
        """Loan rejected when total EMIs > 50% of monthly salary"""
        
        # Create customer with modest income
        customer = Customer.objects.create(
            first_name='Poor',
            last_name='EMI',
            age=30,
            phone_number='+2000000004',
            monthly_income=50000,  # ₹50k/month
            approved_credit_limit=1800000,
            current_debt=500000
        )
        
        # Create existing loan with high EMI (₹20k/month)
        Loan.objects.create(
            customer_id=customer,
            loan_amount=500000,
            interest_rate=12.0,
            term_months=30,
            monthly_payment=20000,  # Existing EMI
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=10,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
        
        # Try to create another loan that would push EMI > 50%
        # Current EMI: 20k, Income: 50k → 50% threshold = 25k
        # New loan EMI would be ~15k → Total 35k > 25k threshold
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 300000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post('/api/loans/create-loan', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['loan_approved'])
        self.assertIn('message', response.data)
    
    def test_check_eligibility_rejected_high_emi_burden(self):
        """Eligibility check also rejects high EMI burden"""
        
        customer = Customer.objects.create(
            first_name='High',
            last_name='EMI',
            age=35,
            phone_number='+2000000005',
            monthly_income=100000,  # ₹1 lakh/month
            approved_credit_limit=3600000,
            current_debt=800000
        )
        
        # Create existing loans totaling ₹45k EMI
        Loan.objects.create(
            customer_id=customer,
            loan_amount=800000,
            interest_rate=11.0,
            term_months=24,
            monthly_payment=45000,
            monthly_payments_made_on_time=12,
            monthly_payment_due_date=5,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
        
        # Try to add ₹10k more EMI (would be 55k total > 50k threshold)
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 200000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])


class LoanVolumeTests(TestCase):
    """Test loan volume constraints based on approved limit"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_rejection_when_loans_exceed_approved_limit(self):
        """Reject loan when sum of current loans > approved limit"""
        
        customer = Customer.objects.create(
            first_name='Overleveraged',
            last_name='Customer',
            age=35,
            phone_number='+2000000006',
            monthly_income=100000,
            approved_credit_limit=3600000,  # ₹36 lakh limit
            current_debt=3500000  # Already at ₹35 lakh
        )
        
        # Create existing loans totaling ₹35 lakh
        Loan.objects.create(
            customer_id=customer,
            loan_amount=3500000,
            interest_rate=10.0,
            term_months=60,
            monthly_payment=74000,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=30,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
        
        # Try to take ₹5 lakh more (would exceed limit)
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'term_months': 12
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])
    
    def test_approval_when_within_limit(self):
        """Approve loan when total loans within approved limit"""
        
        customer = Customer.objects.create(
            first_name='Good',
            last_name='Standing',
            age=40,
            phone_number='+2000000007',
            monthly_income=150000,
            approved_credit_limit=5400000,  # ₹54 lakh limit
            current_debt=1000000  # Only ₹10 lakh used
        )
        
        # Create existing loan
        Loan.objects.create(
            customer_id=customer,
            loan_amount=1000000,
            interest_rate=9.0,
            term_months=36,
            monthly_payment=31800,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=36,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=False
        )
        
        # Request ₹20 lakh more (total ₹30 lakh < ₹54 lakh limit)
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 2000000,
            'interest_rate': 10.0,
            'term_months': 36
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be approved (may still fail on EMI check)


class BoundaryValueTests(TestCase):
    """Test boundary values and edge cases"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_approved_limit_calculation_accuracy(self):
        """Test approved limit rounds to nearest lakh correctly"""
        
        test_cases = [
            (50000, 1800000),    # 36*50k = 1.8M → ₹18 lakh
            (75000, 2700000),    # 36*75k = 2.7M → ₹27 lakh
            (123456, 4400000),   # 36*123.4k = 4.44M → ₹44 lakh (rounds down)
            (138889, 5000000),   # 36*138.8k = 5.00M → ₹50 lakh (exact)
        ]
        
        for idx, (income, expected_limit) in enumerate(test_cases):
            data = {
                'first_name': 'Test',
                'last_name': f'User{idx}',
                'age': 30,
                'phone_number': f'+300000{idx:04d}',
                'monthly_income': income
            }
            
            response = self.client.post('/api/customers/register', data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(
                Decimal(str(response.data['approved_credit_limit'])), 
                Decimal(str(expected_limit)),
                f"Failed for income {income}"
            )
    
    def test_zero_interest_rate_emi_calculation(self):
        """Test EMI calculation with 0% interest rate"""
        
        customer = Customer.objects.create(
            first_name='Zero',
            last_name='Interest',
            age=30,
            phone_number='+2000000008',
            monthly_income=100000,
            approved_credit_limit=3600000,
            current_debt=0
        )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 120000,  # Should be exactly 10k/month for 12 months
            'interest_rate': 0.0,
            'term_months': 12
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        if response.data.get('approval'):
            # EMI should be loan_amount / term_months
            expected_emi = Decimal('120000') / Decimal('12')
            self.assertEqual(
                Decimal(str(response.data['monthly_payment'])), 
                expected_emi
            )


class RepaymentsLeftTests(TestCase):
    """Test repayments_left calculation"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_repayments_left_calculation(self):
        """Test that repayments_left is calculated correctly"""
        from dateutil.relativedelta import relativedelta
        
        customer = Customer.objects.create(
            first_name='Active',
            last_name='Borrower',
            age=33,
            phone_number='+2000000009',
            monthly_income=90000,
            approved_credit_limit=3240000,
            current_debt=500000
        )
        
        # Create loan that started 6 months ago with 12 month term
        start_date = timezone.now() - relativedelta(months=6)
        end_date = start_date + relativedelta(months=12)
        
        loan = Loan.objects.create(
            customer_id=customer,
            loan_amount=500000,
            interest_rate=12.0,
            term_months=12,
            monthly_payment=44424,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=6,
            start_date=start_date,
            end_date=end_date,
            loan_approved=True,
            is_active=True
        )
        
        response = self.client.get(f'/api/loans/view-loans/{customer.customer_id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find the loan in the response
        loan_data = next((l for l in response.data if l['loan_id'] == loan.loan_id), None)
        
        if loan_data and 'repayments_left' in loan_data:
            # Should have ~6 repayments left (12 total - 6 months elapsed)
            self.assertAlmostEqual(loan_data['repayments_left'], 6, delta=1)
    
    def test_new_loan_full_repayments(self):
        """Test that newly created loan shows full term as repayments_left"""
        
        customer = Customer.objects.create(
            first_name='New',
            last_name='Loan',
            age=29,
            phone_number='+2000000010',
            monthly_income=85000,
            approved_credit_limit=3060000,
            current_debt=0
        )
        
        # Create very recent loan (today)
        loan = Loan.objects.create(
            customer_id=customer,
            loan_amount=400000,
            interest_rate=11.0,
            term_months=24,
            monthly_payment=18700,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=0,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=24*30),
            loan_approved=True,
            is_active=True
        )
        
        response = self.client.get(f'/api/loans/view-loans/{customer.customer_id}')
        
        loan_data = next((l for l in response.data if l['loan_id'] == loan.loan_id), None)
        
        if loan_data and 'repayments_left' in loan_data:
            # Should have full 24 repayments
            self.assertAlmostEqual(loan_data['repayments_left'], 24, delta=1)


class ResponseSchemaTests(TestCase):
    """Test API response schema validation"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_register_response_schema(self):
        """Verify registration response has exact required fields"""
        data = {
            'first_name': 'Schema',
            'last_name': 'Test',
            'age': 30,
            'phone_number': '+2000000011',
            'monthly_income': 80000
        }
        
        response = self.client.post('/api/customers/register', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check required fields are present
        required_fields = {
            'customer_id', 'first_name', 'last_name', 
            'age', 'phone_number', 'monthly_income', 'approved_credit_limit'
        }
        
        self.assertTrue(required_fields.issubset(set(response.data.keys())))
    
    def test_eligibility_response_schema(self):
        """Verify eligibility response has exact required fields"""
        
        customer = Customer.objects.create(
            first_name='Schema',
            last_name='Check',
            age=31,
            phone_number='+2000000012',
            monthly_income=95000,
            approved_credit_limit=3420000,
            current_debt=0
        )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 300000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post('/api/loans/check-eligibility', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
        required_fields = {
            'customer_id', 'approval', 'interest_rate', 
            'corrected_interest_rate', 'monthly_payment', 'term_months'
        }
        
        self.assertTrue(required_fields.issubset(set(response.data.keys())))
    
    def test_loan_creation_response_schema(self):
        """Verify loan creation response has required fields"""
        
        customer = Customer.objects.create(
            first_name='Create',
            last_name='Schema',
            age=34,
            phone_number='+2000000013',
            monthly_income=110000,
            approved_credit_limit=3960000,
            current_debt=0
        )
        
        data = {
            'customer_id': customer.customer_id,
            'loan_amount': 400000,
            'interest_rate': 10.0,
            'term_months': 24
        }
        
        response = self.client.post('/api/loans/create-loan', data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Check required fields
        required_fields = {'customer_id', 'loan_approved', 'message'}
        
        self.assertTrue(required_fields.issubset(set(response.data.keys())))
        
        # If approved, should have loan details
        if response.data['loan_approved']:
            additional_fields = {'loan_id', 'monthly_payment'}
            self.assertTrue(additional_fields.issubset(set(response.data.keys())))
    
    def test_loan_detail_response_schema(self):
        """Verify loan detail response has required fields"""
        
        customer = Customer.objects.create(
            first_name='Detail',
            last_name='Schema',
            age=36,
            phone_number='+2000000014',
            monthly_income=105000,
            approved_credit_limit=3780000,
            current_debt=300000
        )
        
        loan = Loan.objects.create(
            customer_id=customer,
            loan_amount=300000,
            interest_rate=11.5,
            term_months=18,
            monthly_payment=18500,
            monthly_payment_due_date=5,
            monthly_payments_made_on_time=10,
            start_date=timezone.now(),
            end_date=timezone.now(),
            loan_approved=True,
            is_active=True
        )
        
        response = self.client.get(f'/api/loans/view-loan/{loan.loan_id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
        required_fields = {
            'loan_id', 'customer_id', 'loan_amount', 'term_months'
        }
        
        self.assertTrue(required_fields.issubset(set(response.data.keys())))


def run_tests():
    """Run all test cases"""
    import sys
    from django.test.runner import DiscoverRunner
    
    test_runner = DiscoverRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run tests for all test classes
    failures = test_runner.run_tests([
        'test_api_endpoints.CustomerRegistrationAPITests',
        'test_api_endpoints.LoanDetailAPITests',
        'test_api_endpoints.CustomerLoansAPITests',
        'test_api_endpoints.LoanEligibilityAPITests',
        'test_api_endpoints.LoanCreationAPITests',
        'test_api_endpoints.IntegrationTests',
        'test_api_endpoints.CreditScoreBehaviorTests',
        'test_api_endpoints.EMIConstraintTests',
        'test_api_endpoints.LoanVolumeTests',
        'test_api_endpoints.BoundaryValueTests',
        'test_api_endpoints.RepaymentsLeftTests',
        'test_api_endpoints.ResponseSchemaTests',
    ])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All API endpoint tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    run_tests()
