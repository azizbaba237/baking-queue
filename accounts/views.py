from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from accounts.models import Client

class RoleBasedLoginView(LoginView):
    """
    Redirige l'utilisateur vers une page différente selon son rôle après login.
    """
    template_name = "registration/login.html" # Chemin vers le template de login

    def get_success_url(self):
        user = self.request.user

        if getattr(user, "role", None) == "admin":
            return reverse_lazy("queue_system:admin_dashboard")
        elif user.role == "employee":
            return reverse_lazy("queue_system:employee_dashboard")
        else:  # client ou rôle inconnu
            return reverse_lazy("queue_system:home")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        client_type = request.POST.get("client_type")

        valid_types = dict(Client.CLIENT_TYPES).keys()
        if not client_type or client_type not in valid_types:
            form.add_error("client_type", "Veuillez sélectionner un type de client valide.")

        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'client'
            user.save()

            # Création du profil client ici uniquement
            if not Client.objects.filter(user=user).exists():
                Client.objects.create(user=user, client_type=client_type)

            login(request, user)
            return redirect("queue_system:home")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/register.html", {
        "form": form,
        "client_types": Client.CLIENT_TYPES,
    })





