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
        client_type = request.POST.get('client_type')  # récupère la sélection du type de client

        if form.is_valid() and client_type in dict(Client.CLIENT_TYPES).keys():
            user = form.save()
            
            # Crée le profil client associé
            Client.objects.create(user=user, client_type=client_type)
            
            # Connexion automatique
            login(request, user)
            return redirect("queue_system:home")
        else:
            print(form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'client_types': Client.CLIENT_TYPES,  # on passe les types de client au template
    })

