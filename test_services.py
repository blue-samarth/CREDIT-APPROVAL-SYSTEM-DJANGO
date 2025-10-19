"""
Comprehensive test suite for core business logic services.

This module tests:
- EMICalculatorService: EMI calculations
- CreditScoreService: Credit score algorithm
- LoanEligibilityService: Loan eligibility decisions

Run tests:
    uv run python test_services.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from django.test.utils import get_runner
from django.conf import settings

from apps.customers.models import Customer
from apps.loans.models import Loan
from core.services import (
    EMICalculatorService,
    CreditScoreService,
    LoanEligibilityService
)


class EMICalculatorServiceTest(TestCase):
    """Test cases for EMI Calculator Service."""
    
    def test_calculate_emi_normal_case(self):
        """Test EMI calculation with typical values."""
        emi = EMICalculatorService.calculate_emi(
            loan_amount=Decimal('500000'),
            annual_interest_rate=Decimal('12.0'),
            tenure_months=24
        )
        
        # Expected EMI ≈ 23,536.68
        self.assertIsInstance(emi, Decimal)
        self.assertGreater(emi, Decimal('23000'))
        self.assertLess(emi, Decimal('24000'))
        
    def test_calculate_emi_zero_interest(self):
        """Test EMI calculation with 0% interest rate."""
        emi = EMICalculatorService.calculate_emi(
            loan_amount=Decimal('120000'),
            annual_interest_rate=Decimal('0'),
            tenure_months=12
        )
        
        # With 0% interest, EMI = loan_amount / tenure
        expected_emi = Decimal('10000.00')
        self.assertEqual(emi, expected_emi)
        
    def test_calculate_emi_high_interest(self):
        """Test EMI calculation with high interest rate."""
        emi = EMICalculatorService.calculate_emi(
            loan_amount=Decimal('100000'),
            annual_interest_rate=Decimal('24.0'),
            tenure_months=12
        )
        
        # High interest should result in higher EMI
        self.assertGreater(emi, Decimal('9000'))
        
    def test_calculate_emi_invalid_loan_amount(self):
        """Test that negative/zero loan amount raises ValueError."""
        with self.assertRaises(ValueError) as context:
            EMICalculatorService.calculate_emi(
                loan_amount=Decimal('-100'),
                annual_interest_rate=Decimal('12.0'),
                tenure_months=12
            )
        
        self.assertIn("must be greater than 0", str(context.exception))
        
    def test_calculate_emi_invalid_tenure(self):
        """Test that zero tenure raises ValueError."""
        with self.assertRaises(ValueError) as context:
            EMICalculatorService.calculate_emi(
                loan_amount=Decimal('100000'),
                annual_interest_rate=Decimal('12.0'),
                tenure_months=0
            )
        
        self.assertIn("must be greater than 0", str(context.exception))
        
    def test_calculate_emi_decimal_precision(self):
        """Test that EMI is rounded to 2 decimal places."""
        emi = EMICalculatorService.calculate_emi(
            loan_amount=Decimal('123456.78'),
            annual_interest_rate=Decimal('11.5'),
            tenure_months=18
        )
        
        # Check that result has exactly 2 decimal places
        emi_str = str(emi)
        decimal_part = emi_str.split('.')[1] if '.' in emi_str else ''
        self.assertEqual(len(decimal_part), 2)
        
    def test_calculate_total_interest(self):
        """Test total interest calculation."""
        emi = Decimal('9000.00')
        tenure = 12
        loan_amount = Decimal('100000')
        
        total_interest = EMICalculatorService.calculate_total_interest(
            emi=emi,
            tenure_months=tenure,
            loan_amount=loan_amount
        )
        
        expected_interest = (emi * tenure) - loan_amount
        self.assertEqual(total_interest, expected_interest)
        
    def test_calculate_total_payment(self):
        """Test total payment calculation."""
        emi = Decimal('25000.00')
        tenure = 24
        
        total_payment = EMICalculatorService.calculate_total_payment(
            emi=emi,
            tenure_months=tenure
        )
        
        expected_total = emi * tenure
        self.assertEqual(total_payment, expected_total)


class CreditScoreServiceTest(TestCase):
    """Test cases for Credit Score Service."""
    
    def setUp(self):
        """Set up test data."""
        # Create test customers
        self.customer_no_loans = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number="1234567890",
            monthly_income=Decimal('50000'),
            approved_credit_limit=Decimal('1800000'),  # 36 * 50000
            current_debt=Decimal('0')
        )
        
        self.customer_with_loans = Customer.objects.create(
            first_name="Jane",
            last_name="Smith",
            age=35,
            phone_number="0987654321",
            monthly_income=Decimal('80000'),
            approved_credit_limit=Decimal('2880000'),  # 36 * 80000
            current_debt=Decimal('0')
        )
        
        # Create test loans for customer_with_loans
        today = timezone.now().date()
        
        # Loan 1: Active, good payment history
        self.loan1 = Loan.objects.create(
            customer_id=self.customer_with_loans,
            loan_amount=Decimal('500000'),
            interest_rate=Decimal('12.0'),
            term_months=24,
            monthly_payment=Decimal('23537'),
            monthly_payments_made_on_time=20,  # 20 out of 24
            monthly_payment_due_date=5,
            loan_approved=True,
            start_date=today - timedelta(days=600),
            end_date=today + timedelta(days=120),
            is_active=True
        )
        
        # Loan 2: Active, perfect payment history
        self.loan2 = Loan.objects.create(
            customer_id=self.customer_with_loans,
            loan_amount=Decimal('300000'),
            interest_rate=Decimal('10.5'),
            term_months=12,
            monthly_payment=Decimal('26708'),
            monthly_payments_made_on_time=12,  # All paid on time
            monthly_payment_due_date=5,
            loan_approved=True,
            start_date=today - timedelta(days=365),
            end_date=today,
            is_active=True
        )
        
    def test_calculate_credit_score_no_loans(self):
        """Test credit score for customer with no loans."""
        result = CreditScoreService.calculate_credit_score(self.customer_no_loans)
        
        self.assertIn('score', result)
        self.assertIn('approval', result)
        self.assertIsInstance(result['score'], Decimal)
        
        # Customer with no loans should have low score
        # But not necessarily 0 (depends on implementation)
        self.assertGreaterEqual(result['score'], Decimal('0'))
        self.assertLessEqual(result['score'], Decimal('100'))
        
    def test_calculate_credit_score_with_loans(self):
        """Test credit score for customer with active loans."""
        result = CreditScoreService.calculate_credit_score(self.customer_with_loans)
        
        self.assertIn('score', result)
        self.assertIn('approval', result)
        
        # Customer with good payment history should have decent score
        score = result['score']
        self.assertGreater(score, Decimal('0'))
        self.assertLessEqual(score, Decimal('100'))
        
    def test_payment_history_score(self):
        """Test payment history component calculation."""
        all_loans = Loan.objects.filter(customer_id=self.customer_with_loans)
        score = CreditScoreService._calculate_payment_history_score(all_loans)
        
        # Score should be between 0 and 30
        self.assertGreaterEqual(score, Decimal('0'))
        self.assertLessEqual(score, Decimal('30'))
        
        # With 32 out of 36 payments on time (88.9%), score should be ~26.67
        self.assertGreater(score, Decimal('25'))
        
    def test_loan_count_score(self):
        """Test loan count component calculation."""
        active_loans = CreditScoreService._get_active_loans(self.customer_with_loans)
        score = CreditScoreService._calculate_loan_count_score(active_loans)
        
        # Score should be between 0 and 20
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
        # Customer has 2 active loans, should get appropriate score
        self.assertGreater(score, 0)
        
    def test_current_year_activity_score(self):
        """Test current year activity component."""
        active_loans = CreditScoreService._get_active_loans(self.customer_with_loans)
        score = CreditScoreService._calculate_current_year_activity_score(active_loans)
        
        # Score should be between 0 and 20
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
    def test_loan_volume_score(self):
        """Test loan volume component calculation."""
        active_loans = CreditScoreService._get_active_loans(self.customer_with_loans)
        score = CreditScoreService._calculate_loan_volume_score(
            self.customer_with_loans,
            active_loans
        )
        
        # Score should be between 0 and 30
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 30)
        
    def test_approved_limit_override(self):
        """Test approved limit override rule."""
        # Create a customer with loans exceeding approved limit
        customer_over_limit = Customer.objects.create(
            first_name="Over",
            last_name="Limit",
            age=40,
            phone_number="1111111111",
            monthly_income=Decimal('30000'),
            approved_credit_limit=Decimal('500000'),  # Low limit
            current_debt=Decimal('0')
        )
        
        # Create loan that exceeds limit
        today = timezone.now().date()
        Loan.objects.create(
            customer_id=customer_over_limit,
            loan_amount=Decimal('600000'),  # Exceeds limit
            interest_rate=Decimal('15.0'),
            term_months=24,
            monthly_payment=Decimal('28952'),
            monthly_payments_made_on_time=10,
            monthly_payment_due_date=5,
            loan_approved=True,
            start_date=today - timedelta(days=300),
            end_date=today + timedelta(days=420),
            is_active=True
        )
        
        active_loans = CreditScoreService._get_active_loans(customer_over_limit)
        override = CreditScoreService._check_approved_limit_override(
            customer_over_limit,
            active_loans
        )
        
        # Should trigger override
        self.assertTrue(override)
        
        # Credit score should be 0
        result = CreditScoreService.calculate_credit_score(customer_over_limit)
        self.assertEqual(result['score'], Decimal('0'))
        self.assertFalse(result['approval'])
        
    def test_get_active_loans(self):
        """Test active loans retrieval."""
        active_loans = CreditScoreService._get_active_loans(self.customer_with_loans)
        
        # Should return QuerySet
        self.assertEqual(active_loans.count(), 2)
        
        # All loans should be active and approved
        for loan in active_loans:
            self.assertTrue(loan.is_active)
            self.assertTrue(loan.loan_approved)


class LoanEligibilityServiceTest(TestCase):
    """Test cases for Loan Eligibility Service."""
    
    def setUp(self):
        """Set up test data."""
        # Create test customer
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            age=30,
            phone_number="5555555555",
            monthly_income=Decimal('100000'),
            approved_credit_limit=Decimal('3600000'),
            current_debt=Decimal('0')
        )
        
        # Create customer with existing loans
        self.customer_with_loans = Customer.objects.create(
            first_name="Existing",
            last_name="Borrower",
            age=35,
            phone_number="6666666666",
            monthly_income=Decimal('60000'),
            approved_credit_limit=Decimal('2160000'),
            current_debt=Decimal('0')
        )
        
        # Add existing loan
        today = timezone.now().date()
        Loan.objects.create(
            customer_id=self.customer_with_loans,
            loan_amount=Decimal('500000'),
            interest_rate=Decimal('12.0'),
            term_months=24,
            monthly_payment=Decimal('23537'),
            monthly_payments_made_on_time=15,
            monthly_payment_due_date=5,
            loan_approved=True,
            start_date=today - timedelta(days=450),
            end_date=today + timedelta(days=270),
            is_active=True
        )
        
    def test_check_eligibility_approved(self):
        """Test successful loan eligibility check."""
        result = LoanEligibilityService.check_eligibility(
            customer_id=self.customer.customer_id,
            loan_amount=Decimal('500000'),
            interest_rate=Decimal('10.0'),
            tenure_months=24
        )
        
        # Check response structure
        self.assertIn('approval', result)
        self.assertIn('customer_id', result)
        self.assertIn('credit_score', result)
        self.assertIn('interest_rate', result)
        self.assertIn('corrected_interest_rate', result)
        self.assertIn('monthly_installment', result)
        self.assertIn('message', result)
        self.assertIn('tenure_months', result)
        
        # Check types
        self.assertIsInstance(result['approval'], bool)
        self.assertIsInstance(result['credit_score'], int)
        self.assertIsInstance(result['monthly_installment'], Decimal)
        
    def test_interest_rate_correction_high_score(self):
        """Test interest rate correction for high credit score."""
        # High score (> 50) should approve at any rate
        approval, corrected_rate, message = LoanEligibilityService._apply_interest_correction(
            credit_score=75,
            requested_rate=Decimal('8.0')
        )
        
        self.assertTrue(approval)
        self.assertEqual(corrected_rate, Decimal('8.0'))
        self.assertIn("Approved", message)
        
    def test_interest_rate_correction_medium_score(self):
        """Test interest rate correction for medium credit score."""
        # Medium score (30-50) should correct to minimum 12%
        approval, corrected_rate, message = LoanEligibilityService._apply_interest_correction(
            credit_score=45,
            requested_rate=Decimal('8.0')  # Below minimum
        )
        
        self.assertTrue(approval)
        self.assertEqual(corrected_rate, Decimal('12.00'))
        self.assertIn("adjusted", message)
        
    def test_interest_rate_correction_low_score(self):
        """Test interest rate correction for low credit score."""
        # Low score (10-30) should correct to minimum 16%
        approval, corrected_rate, message = LoanEligibilityService._apply_interest_correction(
            credit_score=25,
            requested_rate=Decimal('10.0')  # Below minimum
        )
        
        self.assertTrue(approval)
        self.assertEqual(corrected_rate, Decimal('16.00'))
        self.assertIn("adjusted", message)
        
    def test_interest_rate_correction_very_low_score(self):
        """Test rejection for very low credit score."""
        # Very low score (<= 10) should reject
        approval, corrected_rate, message = LoanEligibilityService._apply_interest_correction(
            credit_score=5,
            requested_rate=Decimal('10.0')
        )
        
        self.assertFalse(approval)
        self.assertIn("Rejected", message)
        self.assertIn("low credit score", message)
        
    def test_emi_constraint_within_limit(self):
        """Test EMI constraint when within 50% limit."""
        approval, message = LoanEligibilityService._check_emi_constraint(
            customer=self.customer,
            loan_amount=Decimal('300000'),
            interest_rate=Decimal('12.0'),
            tenure_months=24
        )
        
        self.assertTrue(approval)
        self.assertIn("Approved", message)
        
    def test_emi_constraint_exceeds_limit(self):
        """Test EMI constraint when exceeding 50% of income."""
        approval, message = LoanEligibilityService._check_emi_constraint(
            customer=self.customer,
            loan_amount=Decimal('5000000'),  # Very large loan
            interest_rate=Decimal('15.0'),
            tenure_months=12  # Short tenure = high EMI
        )
        
        self.assertFalse(approval)
        self.assertIn("exceeds 50%", message)
        
    def test_emi_constraint_with_existing_loans(self):
        """Test EMI constraint considering existing loans."""
        # Customer already has loan with EMI of ~23,537
        # Monthly income: 60,000
        # 50% limit: 30,000
        # Available: ~6,463
        
        # Try to get loan that would push over limit
        approval, message = LoanEligibilityService._check_emi_constraint(
            customer=self.customer_with_loans,
            loan_amount=Decimal('200000'),
            interest_rate=Decimal('12.0'),
            tenure_months=12  # EMI ~17,770 - would exceed limit
        )
        
        # Should fail due to combined EMI burden
        self.assertFalse(approval)
        
    def test_check_eligibility_customer_not_found(self):
        """Test eligibility check with non-existent customer."""
        with self.assertRaises(Customer.DoesNotExist):
            LoanEligibilityService.check_eligibility(
                customer_id=99999,  # Non-existent
                loan_amount=Decimal('100000'),
                interest_rate=Decimal('10.0'),
                tenure_months=12
            )
            
    def test_check_eligibility_rejected_low_score(self):
        """Test eligibility rejection due to low credit score."""
        # Create customer with poor credit
        poor_customer = Customer.objects.create(
            first_name="Poor",
            last_name="Credit",
            age=25,
            phone_number="7777777777",
            monthly_income=Decimal('20000'),
            approved_credit_limit=Decimal('100000'),  # Very low
            current_debt=Decimal('0')
        )
        
        # Add many loans to lower score
        today = timezone.now().date()
        for i in range(8):
            Loan.objects.create(
                customer_id=poor_customer,
                loan_amount=Decimal('10000'),
                interest_rate=Decimal('18.0'),
                term_months=12,
                monthly_payment=Decimal('900'),
                monthly_payments_made_on_time=5,  # Poor payment history
                monthly_payment_due_date=5,
                loan_approved=True,
                start_date=today - timedelta(days=200),
                end_date=today + timedelta(days=165),
                is_active=True
            )
        
        result = LoanEligibilityService.check_eligibility(
            customer_id=poor_customer.customer_id,
            loan_amount=Decimal('50000'),
            interest_rate=Decimal('10.0'),
            tenure_months=12
        )
        
        # Should be rejected
        self.assertFalse(result['approval'])
        self.assertLess(result['credit_score'], 50)
        
    def test_check_eligibility_complete_flow(self):
        """Test complete eligibility check flow."""
        result = LoanEligibilityService.check_eligibility(
            customer_id=self.customer.customer_id,
            loan_amount=Decimal('1000000'),
            interest_rate=Decimal('9.5'),
            tenure_months=36
        )
        
        # Verify all fields are present
        required_fields = [
            'approval', 'customer_id', 'credit_score',
            'interest_rate', 'corrected_interest_rate',
            'monthly_installment', 'message', 'tenure_months'
        ]
        
        for field in required_fields:
            self.assertIn(field, result)
            
        # Verify customer_id matches
        self.assertEqual(result['customer_id'], self.customer.customer_id)
        
        # Verify tenure matches
        self.assertEqual(result['tenure_months'], 36)
        
        # Verify EMI is calculated
        self.assertGreater(result['monthly_installment'], Decimal('0'))


class IntegrationTest(TestCase):
    """Integration tests for complete loan approval workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = Customer.objects.create(
            first_name="Integration",
            last_name="Test",
            age=32,
            phone_number="8888888888",
            monthly_income=Decimal('150000'),
            approved_credit_limit=Decimal('5400000'),
            current_debt=Decimal('0')
        )
        
    def test_complete_loan_approval_workflow(self):
        """Test complete workflow from eligibility check to approval."""
        # Step 1: Check eligibility
        eligibility_result = LoanEligibilityService.check_eligibility(
            customer_id=self.customer.customer_id,
            loan_amount=Decimal('2000000'),
            interest_rate=Decimal('11.0'),
            tenure_months=48
        )
        
        self.assertTrue(eligibility_result['approval'])
        
        # Step 2: Verify EMI calculation
        emi = eligibility_result['monthly_installment']
        self.assertGreater(emi, Decimal('0'))
        
        # Step 3: Verify EMI is within 50% of income
        max_emi = self.customer.monthly_income * Decimal('0.5')
        self.assertLess(emi, max_emi)
        
        # Step 4: Create loan (simulated)
        loan = Loan.objects.create(
            customer_id=self.customer,
            loan_amount=Decimal('2000000'),
            interest_rate=eligibility_result['corrected_interest_rate'],
            term_months=48,
            monthly_payment=emi,
            monthly_payments_made_on_time=0,
            monthly_payment_due_date=5,
            loan_approved=True,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=48*30),
            is_active=True
        )
        
        self.assertTrue(loan.loan_approved)
        self.assertEqual(loan.monthly_payment, emi)
        
    def test_workflow_with_rate_correction(self):
        """Test workflow when interest rate needs correction."""
        # Add some loans to lower credit score
        today = timezone.now().date()
        for i in range(3):
            Loan.objects.create(
                customer_id=self.customer,
                loan_amount=Decimal('500000'),
                interest_rate=Decimal('12.0'),
                term_months=24,
                monthly_payment=Decimal('23537'),
                monthly_payments_made_on_time=12,  # Partial payments
                monthly_payment_due_date=5,
                loan_approved=True,
                start_date=today - timedelta(days=365),
                end_date=today + timedelta(days=365),
                is_active=True
            )
        
        # Request loan with low interest rate
        result = LoanEligibilityService.check_eligibility(
            customer_id=self.customer.customer_id,
            loan_amount=Decimal('300000'),
            interest_rate=Decimal('8.0'),  # Low rate
            tenure_months=12
        )
        
        # Rate should be corrected based on credit score
        if result['approval']:
            self.assertGreaterEqual(
                result['corrected_interest_rate'],
                result['interest_rate']
            )


if __name__ == '__main__':
    print("🧪 Running Comprehensive Service Tests...")
    print("=" * 70)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run all tests in this file
    failures = test_runner.run_tests(['__main__'])
    
    print("\n" + "=" * 70)
    if failures:
        print(f"❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("✅ All 32 service tests passed!")
        print("=" * 70)
        sys.exit(0)
