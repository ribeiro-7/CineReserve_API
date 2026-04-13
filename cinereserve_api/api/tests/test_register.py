from rest_framework import test
from django.urls import reverse

class RegisterTest(test.APITestCase):
    
    def test_register_user_201_created(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testpassword123#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            201
        )
        self.assertEqual(
            response.data.get('email'),
            email
        )
        self.assertEqual(
            response.data.get('username'),
            username
        )

    def test_register_user_with_invalid_email_error_400(self):
        email = 'usertest1'
        username = 'usertest'
        password = 'Testpassword123#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('email')[0],
            "Enter a valid email address."
        )

    def test_register_user_with_password_without_upper_case_error_400(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'testpassword123#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('password')[0],
            "A senha precisar conter pelo menos uma letra maiúscula."
        )

    def test_register_user_with_password_without_a_special_caracter_error_400(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testpassword123'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('password')[0],
            "A senha precisa conter pelo menos um caracter especial"
        )

    def test_register_user_with_password_without_a_special_caracter_error_400(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testpassword123'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('password')[0],
            "A senha precisa conter pelo menos um caracter especial"
        )

    def test_register_user_with_password_without_a_number_error_400(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testpassword#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('password')[0],
            "A senha precisar conter pelo menos um caracter numérico."
        )
    
    def test_register_user_with_less_than_8_caracters_password_error_400(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testp1#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('password')[0],
            "A senha precisar tem no mínimo 8 caracteres."      
        )