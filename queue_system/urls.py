from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from accounts.views import RoleBasedLoginView 

app_name = 'queue_system'

urlpatterns = [
    # --- SECTION CLIENT / PUBLIC ---
    path("", views.home, name="home"),
    path("take-ticket/<int:service_id>/", views.take_ticket, name="take_ticket"),
    path("ticket/<int:ticket_id>/", views.ticket_status, name="ticket_status"),
    path('ticket/<int:ticket_id>/wait-time/', views.get_estimated_wait_time, name='get_estimated_wait_time'),
    path('ticket/<int:ticket_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),
    path('waiting-room/<int:ticket_id>/', views.waiting_room, name='waiting_room'),
    path("employee/ticket/<int:ticket_id>/complete/", views.complete_ticket, name="complete_ticket"),
    path("ticket/completed/<int:ticket_id>/", views.ticket_completed, name="ticket_completed"),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),

    # --- SECTION AUTHENTIFICATION (si tu ne veux pas passer par accounts) ---
    path("login/", RoleBasedLoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(
        next_page="queue_system:home"
    ), name="logout"),
    #path("register/", views.register, name="register"),  # Si tu veux aussi un register ici

    # --- SECTION PROFIL UTILISATEUR ---
    path("profile/<int:pk>/", views.profile_view, name="profile"),
    path("profile/activity/", views.profile_activity, name="profile_activity"),
    path("profile/delete/", views.delete_account, name="delete_account"),
    path("ajax/check-email/", views.check_email_availability, name="check_email"),

    # --- SECTION EMPLOYÉ (TABLEAU DE BORD) ---
    path("employee/", views.employee_dashboard, name="employee_dashboard"),
    path("employee/call-next/", views.call_next_ticket, name="call_next_ticket"),
    path("employee/ticket/<int:ticket_id>/call/", views.call_ticket, name="call_ticket"),
    path("employee/ticket/<int:ticket_id>/start/", views.start_service, name="start_service"),
    path("employee/ticket/<int:ticket_id>/complete/", views.complete_ticket, name="complete_ticket"),
    path("employee/ticket/<int:ticket_id>/cancel/", views.cancel_ticket, name="cancel_ticket"),

    # --- SECTION ADMIN ---
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path("admin/user/<int:user_id>/", views.admin_user_profile, name="admin_user_profile"),

    # --- SECTION API ---
    path("api/call-next/", views.call_next_client, name="call_next_client"),
    
]
