from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm  # <-- le bon formulaire
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from accounts.models import Client


class RoleBasedLoginView(LoginView):
    """
    Redirige l'utilisateur vers une page différente selon son rôle après login.
    """
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user

        if getattr(user, "role", None) == "admin":
            return reverse_lazy("queue_system:admin_dashboard")
        elif user.role == "employee":
            return reverse_lazy("queue_system:employee_dashboard")
        else:
            return reverse_lazy("queue_system:home")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)  # <- Utilisation correcte
        if form.is_valid():
            user = form.save()  # le formulaire crée le Client automatiquement
            login(request, user)
            return redirect("queue_system:home")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/register.html", {
        "form": form,
        "client_types": Client.CLIENT_TYPES,
    })
