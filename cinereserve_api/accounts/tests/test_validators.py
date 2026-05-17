from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.validators import email_validator, password_validator

User = get_user_model()


class ValidatorsTest(TestCase):
    def test_password_validator_requires_minimum_length(self):
        with self.assertRaises(ValidationError) as ctx:
            password_validator('Ab1!')
        self.assertIn('8 characters', str(ctx.exception))

    def test_password_validator_requires_number(self):
        with self.assertRaises(ValidationError) as ctx:
            password_validator('Password!')
        self.assertIn('numeric', str(ctx.exception))

    def test_password_validator_requires_uppercase(self):
        with self.assertRaises(ValidationError) as ctx:
            password_validator('password1!')
        self.assertIn('upper case', str(ctx.exception))

    def test_password_validator_requires_special_character(self):
        with self.assertRaises(ValidationError) as ctx:
            password_validator('Password1')
        self.assertIn('special character', str(ctx.exception))

    def test_password_validator_accepts_valid_password(self):
        password_validator('Password1!')

    def test_email_validator_rejects_duplicate(self):
        User.objects.create_user(
            username='existing',
            email='taken@test.com',
            password='Password1!',
        )
        with self.assertRaises(ValidationError) as ctx:
            email_validator('Taken@Test.com')
        self.assertIn('already exists', str(ctx.exception))

    def test_email_validator_returns_lowercase_email(self):
        result = email_validator('new@test.com')
        self.assertEqual(result, 'new@test.com')
