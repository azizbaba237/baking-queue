from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User, Client, Employee


# Génération automatique d'un ID employé
def generate_employee_id():
    count = Employee.objects.count() + 1
    return f"EMP-{count:04d}"


# Formulaire pour les clients
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=20)

    client_type = forms.ChoiceField(choices=Client.CLIENT_TYPES, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['first_name'].widget.attrs.update({'placeholder': 'Prénom'})
            self.fields['last_name'].widget.attrs.update({'placeholder': 'Nom'})
            self.fields['email'].widget.attrs.update({'placeholder': 'Email'})
            self.fields['phone'].widget.attrs.update({'placeholder': 'Téléphone'})
            self.fields['username'].widget.attrs.update({'placeholder': 'Nom d’utilisateur'})
            self.fields['password1'].widget.attrs.update({'placeholder': 'Mot de passe'})
            self.fields['password2'].widget.attrs.update({'placeholder': 'Confirmer le mot de passe'})
            self.fields['employee_id'].widget.attrs.update({'placeholder': 'ID Employé (optionnel)'})
            self.fields['hire_date'].widget.attrs.update({'placeholder': 'Date d’embauche'})
            
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data["phone"]
        user.role = 'client'

        if commit:
            user.save()
            Client.objects.create(
                user=user,
                client_type=self.cleaned_data["client_type"]
            )

        return user


# Formulaire pour les employés
class EmployeeCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=20)

    employee_id = forms.CharField(
        required=False,
        initial=generate_employee_id,
        help_text="Laisser vide pour générer automatiquement"
    )
    hire_date = forms.DateField(
        required=True,
        widget=forms.SelectDateWidget(years=range(timezone.now().year - 10, timezone.now().year + 1))
    )
    status = forms.ChoiceField(
        choices=Employee.STATUS_CHOICES,
        initial='offline',
        required=True
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2", "employee_id", "hire_date", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Prénom'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Nom'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'Téléphone'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Nom d’utilisateur'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirmer le mot de passe'})
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data["phone"]
        user.role = 'employee'

        if commit:
            user.save()

            emp_id = self.cleaned_data.get("employee_id") or generate_employee_id()

            Employee.objects.create(
                user=user,
                employee_id=emp_id,
                hire_date=self.cleaned_data["hire_date"],
                status=self.cleaned_data["status"],
            )

        return user
