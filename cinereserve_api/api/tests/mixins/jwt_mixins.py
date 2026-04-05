from django.urls import reverse
from django.contrib.auth import get_user_model

class JWTMixin:
    def make_user(self, username, password):
        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            password=password
        )
        return user
    
    def make_super_user(self, username, password):
        User = get_user_model()
        super_user = User.objects.create_superuser(
            username=username,
            password=password
        )
        return super_user

            
    def get_user_access_token(self):
        user_data = {
            'username': 'usertest',
            'password': 'Password123#'
        }
        self.make_user(username=user_data.get('username'), password=user_data.get('password'))
        api_url = reverse('token_obtain_pair')
        response = self.client.post(api_url, user_data, format='json')
        acess_token = response.data.get('access')
        return acess_token
    
    def get_admin_access_token(self):
        super_user_data = {
            'username': 'admin',
            'password': 'Admin123#'
        }
        self.make_super_user(username=super_user_data.get('username'), password=super_user_data.get('password'))
        api_url = reverse('token_obtain_pair')
        response = self.client.post(api_url, super_user_data, format='json')
        access_token = response.data.get('access')
        return access_token