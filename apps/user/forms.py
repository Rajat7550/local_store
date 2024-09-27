from django import forms
from .models import User, Product


class StoreDetails(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']

class UserCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','email','password']

class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email','password']