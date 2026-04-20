from rest_framework import test
from django.urls import reverse
from .mixins import jwt_mixins
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.utils import timezone
from datetime import timedelta
import time

class AccountsTest(test.APITestCase, jwt_mixins.JWTMixin):
    
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
            "Password must contain at least one upper case character."
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
            "Password must contain at least one special character."
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
            "Password must contain at least one numeric character."
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
            "Password must contain at least 8 characters."      
        )

    def test_user_who_tries_to_create_an_account_with_email_thats_already_has_account_with(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testp10#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        self.client.post(api_url, data=data)
        email2 = 'usertest@gmail.com'
        username2 = 'user2test'
        password2 = 'Testp10#'
        data2 = {
            'email': email2,
            'username': username2,
            'password': password2
        }
        response = self.client.post(api_url, data=data2)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('email')[0],
            "An account already exists with that email."
        )
    
    def test_if_login_returns_refresh_and_acess_token_and_code_200_ok(self):
        username = self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username=username, password=password)
        self.assertEqual(
            login.status_code,
            200
        )
        self.assertIsNotNone(
            login.data.get('refresh')
        )
        self.assertIsNotNone(
            login.data.get('access')
        )

    def test_if_login_with_wrong_password_returns_right_error_message_and_code_401_unauthorized(self):
        username = self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10'}
        login = self.login_user(username=username, password=password)
        self.assertEqual(
            login.status_code,
            401
        )
        self.assertEqual(
            login.data.get('detail'),
            'No active account found with the given credentials'
        )

    def test_if_login_with_wrong_username_returns_right_error_message_and_code_401_unauthorized(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g11_arrascaeta', password=password)
        self.assertEqual(
            login.status_code,
            401
        )
        self.assertEqual(
            login.data.get('detail'),
            'No active account found with the given credentials'
        )

    def test_user_who_tries_to_create_account_with_username_thats_already_has_an_account_with(self):
        email = 'usertest@gmail.com'
        username = 'usertest'
        password = 'Testp10#'
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        api_url = reverse('register')
        self.client.post(api_url, data=data)
        email2 = 'usertest2@gmail.com'
        username2 = 'usertest'
        password2 = 'Testp10#'
        data2 = {
            'email': email2,
            'username': username2,
            'password': password2
        }
        response = self.client.post(api_url, data=data2)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data.get('username')[0],
            "A user with that username already exists."
        )
        
    #Refresh tests
    def test_if_refresh_token_return_new_access_token_200_ok(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        refresh_token = login.data.get('refresh')
        response, access_token = self.refresh_token(refresh_token=refresh_token)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIsNotNone(
            access_token
        )

    def test_if_refresh_token_return_error_with_invalid_refresh_token_code_401(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        refresh_token = login.data.get('refresh')
        refresh_token = refresh_token + '0m'
        response, _ = self.refresh_token(refresh_token=refresh_token)
        self.assertEqual(
            response.status_code,
            401
        )
        self.assertEqual(
            response.data.get('detail'),
            'Token is invalid'
        )
        self.assertEqual(
            response.data.get('code'),
            'token_not_valid'
        )

    #Verify tests
    def test_if_verify_token_return_code_200_ok_to_valid_access_token(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        access_token = login.data.get('access')
        data={
            'token': access_token
        }
        api_url = reverse('token_verify')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            200
        )

    def test_if_verify_token_with_invalid_access_token_return_code_401_unauthorized(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        access_token = login.data.get('access')
        access_token = access_token + '0m'
        data={
            'token': access_token
        }
        api_url = reverse('token_verify')
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            401
        )
        self.assertEqual(
            response.data.get('detail'),
            'Token is invalid'
        )
        self.assertEqual(
            response.data.get('code'),
            'token_not_valid'
        )

    def test_if_verify_token_with_expired_access_token_return_code_401_unauthorized(self):
        user = self.make_user(username='g10_arrascaeta', password='Camisa10$')
        token = AccessToken.for_user(user)
        token.set_exp(from_time=timezone.now(), lifetime=timedelta(seconds=1))
        time.sleep(3)
        api_url = reverse('token_verify')
        data={
            'token': str(token)
        }
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            401
        )
        self.assertEqual(
            response.data.get('detail'),
            'Token is expired'
        )
        self.assertEqual(
            response.data.get('code'),
            'token_not_valid'
        )

    #Logout tests
    def test_if_logout_blacklist_refresh_token_and_return_code_200_ok(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        refresh_token = login.data.get('refresh')
        api_url = reverse('logout')
        data={
            'refresh': refresh_token
        }
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            200
        )

    def test_logout_with_invalid_refresh_token_and_return_code_401_unauthorized(self):
        self.register_user(email='g10arrascaeta@gmail.com', username='g10_arrascaeta', password='Camisa10$')
        password = {'Camisa10$'}
        login = self.login_user(username='g10_arrascaeta', password=password)
        refresh_token = login.data.get('refresh')
        refresh_token = refresh_token + '0m'
        api_url = reverse('logout')
        data={
            'refresh': refresh_token
        }
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            401
        )
        self.assertEqual(
            response.data.get('detail'),
            'Token is invalid'
        )
        self.assertEqual(
            response.data.get('code'),
            'token_not_valid'
        )

    def test_logout_with_expired_refresh_token_and_return_code_401_unauthorized(self):
        user = self.make_user(username='g10_arrascaeta', password='Camisa10$')
        refresh_token = RefreshToken.for_user(user)
        refresh_token.set_exp(from_time=timezone.now(), lifetime=timedelta(seconds=1))
        time.sleep(3)
        api_url = reverse('logout')
        data={
            'refresh': str(refresh_token)
        }
        response = self.client.post(api_url, data=data)
        self.assertEqual(
            response.status_code,
            401
        )
        self.assertEqual(
            response.data.get('detail'),
            'Token is expired'
        )
        self.assertEqual(
            response.data.get('code'),
            'token_not_valid'
        )