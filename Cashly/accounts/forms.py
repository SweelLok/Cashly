from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile


# форма регистрации
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['password1'] != cleaned_data['password2']:
            # проверяем совпадение паролей
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# форма редактирования профиля
class EditProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 4
    }))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    monthly_budget = forms.DecimalField(required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={
        'class': 'form-control'
    }))
    lifetime_budget = forms.DecimalField(required=False, max_digits=15, decimal_places=2, widget=forms.NumberInput(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = UserProfile
        fields = ('bio', 'photo', 'monthly_budget', 'lifetime_budget')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user and (self.cleaned_data.get('username') or self.cleaned_data.get('email')):
            if self.cleaned_data.get('username'):
                self.user.username = self.cleaned_data['username']
            if self.cleaned_data.get('email'):
                self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        return profile
