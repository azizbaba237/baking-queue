from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Client
from django.utils import timezone
from .models import User  # Ton modèle personnalisé


# Optionnel : Générer un ID unique pour les employés
def generate_employee_id():
    count = Employee.objects.count() + 1
    return f"EMP-{count:04d}"

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=20)
    role = forms.ChoiceField(choices=[('client', 'Client'), ('employee', 'Employé')], required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "role", "password1", "password2")

    # Override save pour enregistrer aussi les champs personnalisés
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data["phone"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            
         # Crée un Client ou Employee selon le rôle
        if user.role == "client":
            Client.objects.create(user=user, client_type="regular")  # Tu peux adapter le type
        elif user.role == "employee":
            employee_id = generate_employee_id()
            Employee.objects.create(
                user=user,
                employee_id=employee_id,
                hire_date=timezone.now().date()  # Assure-toi d'importer timezone
            )
        return user
