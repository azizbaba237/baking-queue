from django.urls import path, include
from .views import RoleBasedLoginView
from . import views

app_name = "accounts"

urlpatterns = [
    
    # Login personnalisé
    path("login/", RoleBasedLoginView.as_view(), name="login"),
    
    # Inscription personnalisée
    path("register/", views.register, name="register"),
    
    # Authentification Django classique : login, logout, password reset...
    path("", include("django.contrib.auth.urls")),   
]
