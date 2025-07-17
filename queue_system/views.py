from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import  Avg, F, ExpressionWrapper, DurationField
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Service, Ticket
import uuid
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.paginator import Paginator
import json
import re


# ----------------------------------------------------------------- 

def home(request):
    services = Service.objects.filter(is_active=True)
    return render(request, 'queue_system/home.html', {'services': services})

@login_required
def take_ticket(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    if request.method == 'POST':
        # Vérifier si le client a déjà un ticket en attente
        existing_ticket = Ticket.objects.filter(
            client=request.user.client,
            status__in=['waiting', 'called', 'in_service']
        ).first()
        
        if existing_ticket:
            messages.error(request, 'Vous avez déjà un ticket en cours.')
            return redirect('queue_system:ticket_status', ticket_id=existing_ticket.id)
        
        # Créer un nouveau ticket
        ticket = Ticket.objects.create(
            ticket_number=f"{service.name[:2].upper()}{uuid.uuid4().hex[:6].upper()}",
            client=request.user.client,
            service=service,
            priority=service.base_priority + (10 if request.user.client.client_type == 'vip' else 0)
        )
        
        # Calculer le temps d'attente
        ticket.estimated_wait_time = ticket.calculate_wait_time()
        ticket.save()
        
        messages.success(request, f'Ticket {ticket.ticket_number} créé avec succès!')
        return redirect('queue_system:ticket_status', ticket_id=ticket.id)
    
    return render(request, 'queue_system/take_ticket.html', {'service': service})

@login_required
def ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, client=request.user.client)
    position = ticket.get_position_in_queue()
    
    return render(request, 'queue_system/ticket_status.html', {
        'ticket': ticket,
        'position': position
    })

@api_view(['POST'])
def call_next_client(request):
    if request.user.role != 'employee':
        return Response({'error': 'Non autorisé'}, status=403)
    
    # Obtenir le prochain ticket
    next_ticket = Ticket.objects.filter(status='waiting').first()
    
    if not next_ticket:
        return Response({'message': 'Aucun client en attente'})
    
    # Mettre à jour le ticket
    next_ticket.status = 'called'
    next_ticket.called_at = timezone.now()
    next_ticket.employee = request.user.employee
    next_ticket.save()
    
    # TODO: Envoyer notification au client
    
    return Response({
        'ticket_number': next_ticket.ticket_number,
        'client_name': f"{next_ticket.client.user.first_name} {next_ticket.client.user.last_name}",
        'service': next_ticket.service.name
    })
    
# -----------------------------------------------------------------
#  OUTILS INTERNES
# -----------------------------------------------------------------
def _employee_required(user):
    return getattr(user, "role", None) == "employee"

def _forbid_non_employee(request):
    if not _employee_required(request.user):
        messages.error(request, "Accès non autorisé.")
        return True
    return False


# -----------------------------------------------------------------
#  DASHBOARD EMPLOYÉ
# -----------------------------------------------------------------
@login_required
def employee_dashboard(request):
    if _forbid_non_employee(request):
        return redirect("queue_system:home")

    waiting_tickets = (
        Ticket.objects.filter(status="waiting")
        .select_related("service", "client")
        .order_by("-priority", "created_at")
    )

    current_ticket = (
        Ticket.objects.filter(
            employee=request.user.employee, status__in=["called", "in_service"]
        )
        .order_by("status")      # 'called' d’abord
        .first()
    )

    today = timezone.localdate()
    today_qs = Ticket.objects.filter(created_at__date=today)

    # ── Durée moyenne = (completed_at − created_at) ──
    avg_delta = (
        today_qs.filter(status="completed")
        .annotate(
            delta=ExpressionWrapper(
                F("completed_at") - F("created_at"), output_field=DurationField()
            )
        )
        .aggregate(avg=Avg("delta"))["avg"]
    )
    avg_wait_min = int(avg_delta.total_seconds() // 60) if avg_delta else 0

    stats = {
        "waiting": today_qs.filter(status="waiting").count(),
        "in_service": today_qs.filter(status="in_service").count(),
        "completed": today_qs.filter(status="completed").count(),
        "cancelled": today_qs.filter(status="cancelled").count(),
        "avg_wait": avg_wait_min,
    }

    return render(
        request,
        "queue_system/employee_dashboard.html",
        {
            "waiting_tickets": waiting_tickets,
            "current_ticket": current_ticket,
            "stats": stats,
        },
    )


# -----------------------------------------------------------------
#  ACTIONS SUR LES TICKETS
# -----------------------------------------------------------------
@login_required
@require_POST
def call_next_ticket(request):
    if _forbid_non_employee(request):
        return redirect("queue_system:employee_dashboard")

    ticket = (
        Ticket.objects.filter(status="waiting")
        .order_by("-priority", "created_at")
        .first()
    )
    if not ticket:
        messages.info(request, "Aucun ticket en attente.")
        return redirect("queue_system:employee_dashboard")

    _call_ticket_core(ticket, request.user.employee)
    messages.success(request, f"Ticket {ticket.ticket_number} appelé.")
    return redirect("queue_system:employee_dashboard")


@login_required
@require_POST
def call_ticket(request, ticket_id):
    if _forbid_non_employee(request):
        return redirect("queue_system:employee_dashboard")

    ticket = get_object_or_404(Ticket, id=ticket_id, status="waiting")
    _call_ticket_core(ticket, request.user.employee)
    messages.success(request, f"Ticket {ticket.ticket_number} appelé.")
    return redirect("queue_system:employee_dashboard")


def _call_ticket_core(ticket: Ticket, employee):
    ticket.status = "called"
    ticket.called_at = timezone.now()
    ticket.employee = employee
    ticket.save()


@login_required
@require_POST
def start_service(request, ticket_id):
    if _forbid_non_employee(request):
        return redirect("queue_system:employee_dashboard")

    ticket = get_object_or_404(Ticket, id=ticket_id, status__in=["called", "waiting"])
    ticket.status = "in_service"
    ticket.service_started_at = timezone.now()
    ticket.employee = request.user.employee
    ticket.save()
    messages.success(request, f"Service commencé pour le ticket {ticket.ticket_number}.")
    return redirect("queue_system:employee_dashboard")


@login_required
@require_POST
def complete_ticket(request, ticket_id):
    if _forbid_non_employee(request):
        return redirect("queue_system:employee_dashboard")

    ticket = get_object_or_404(Ticket, id=ticket_id, status="in_service")
    ticket.status = "completed"
    ticket.completed_at = timezone.now()
    ticket.save()
    messages.success(request, f"Ticket {ticket.ticket_number} terminé.")
    return redirect("queue_system:employee_dashboard")


@login_required
@require_POST
def cancel_ticket(request, ticket_id):
    if _forbid_non_employee(request):
        return redirect("queue_system:employee_dashboard")

    ticket = get_object_or_404(
        Ticket, id=ticket_id, status__in=["waiting", "called", "in_service"]
    )
    ticket.status = "cancelled"
    ticket.completed_at = timezone.now()
    ticket.save()
    messages.warning(request, f"Ticket {ticket.ticket_number} annulé.")
    return redirect("queue_system:employee_dashboard")


# Registation view for new users
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirige vers la page d'accueil après inscription
    else:
        form = UserCreationForm()
    return render(request, 'authentification/register.html', {'form': form})


# -----------------------------------------------------------------
#  GESTION DU PROFIL UTILISATEUR
# -----------------------------------------------------------------

@login_required
def profile_view(request):
    """
    Vue pour afficher et gérer le profil utilisateur
    """
    if request.method == 'POST':
        # Vérifier si c'est une mise à jour de profil ou de mot de passe
        if 'current_password' in request.POST:
            return handle_password_change(request)
        else:
            return handle_profile_update(request)
    
    # Récupérer les statistiques pour les clients
    context = {
        'user': request.user,
    }
    
    # Ajouter les statistiques pour les clients
    if hasattr(request.user, 'client') and request.user.role == 'client':
        tickets = request.user.client.ticket_set.all()
        context.update({
            'total_tickets': tickets.count(),
            'completed_tickets': tickets.filter(status='completed').count(),
            'waiting_tickets': tickets.filter(status='waiting').count(),
            'recent_tickets': tickets.order_by('-created_at')[:5],
        })
    
    return render(request, 'queue_system/profile.html', context)


def handle_profile_update(request):
    """
    Gère la mise à jour des informations du profil
    """
    user = request.user
    
    try:
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validation des champs requis
        if not first_name:
            messages.error(request, 'Le prénom est requis.')
            return redirect('queue_system:profile')
        
        if not last_name:
            messages.error(request, 'Le nom est requis.')
            return redirect('queue_system:profile')
        
        if not email:
            messages.error(request, 'L\'email est requis.')
            return redirect('queue_system:profile')
        
        # Validation de l'email
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            messages.error(request, 'Format d\'email invalide.')
            return redirect('queue_system:profile')
        
        # Vérifier si l'email existe déjà pour un autre utilisateur
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Cet email est déjà utilisé par un autre utilisateur.')
            return redirect('queue_system:profile')
        
        # Validation du téléphone (format camerounais)
        if phone:
            # Nettoyer le numéro de téléphone
            phone_clean = re.sub(r'[^\d]', '', phone)
            if phone_clean.startswith('237'):
                phone_clean = phone_clean[3:]
            
            # Vérifier le format (9 chiffres pour le Cameroun)
            if not re.match(r'^\d{9}$', phone_clean):
                messages.error(request, 'Format de téléphone invalide. Utilisez le format camerounais (9 chiffres).')
                return redirect('queue_system:profile')
            
            # Formater le numéro
            phone = f'+237 {phone_clean[:3]} {phone_clean[3:6]} {phone_clean[6:9]}'
        
        # Mettre à jour les informations
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.save()
        
        messages.success(request, 'Profil mis à jour avec succès.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise à jour du profil: {str(e)}')
    
    return redirect('queue_system:profile')


def handle_password_change(request):
    """
    Gère le changement de mot de passe
    """
    user = request.user
    
    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation des champs requis
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, 'Tous les champs sont requis.')
            return redirect('queue_system:profile')
        
        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return redirect('queue_system:profile')
        
        # Vérifier le mot de passe actuel
        if not user.check_password(current_password):
            messages.error(request, 'Mot de passe actuel incorrect.')
            return redirect('queue_system:profile')
        
        # Valider le nouveau mot de passe
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
            return redirect('queue_system:profile')
        
        # Changer le mot de passe
        user.set_password(new_password)
        user.save()
        
        # Maintenir la session utilisateur
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Mot de passe modifié avec succès.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors du changement de mot de passe: {str(e)}')
    
    return redirect('queue_system:profile')


@login_required
@require_http_methods(["POST"])
def check_email_availability(request):
    """
    Vérifie si un email est disponible (pour AJAX)
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({'available': False, 'message': 'Email requis'})
        
        # Vérifier le format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return JsonResponse({'available': False, 'message': 'Format d\'email invalide'})
        
        # Vérifier la disponibilité
        from django.contrib.auth import get_user_model
        User = get_user_model()
        exists = User.objects.filter(email=email).exclude(id=request.user.id).exists()
        
        return JsonResponse({
            'available': not exists,
            'message': 'Email déjà utilisé' if exists else 'Email disponible'
        })
        
    except Exception as e:
        return JsonResponse({'available': False, 'message': 'Erreur de validation'})


@login_required
def profile_activity(request):
    """
    Vue pour afficher toute l'activité utilisateur (page séparée)
    """
    if not (hasattr(request.user, 'client') and request.user.role == 'client'):
        messages.error(request, 'Accès non autorisé.')
        return redirect('queue_system:profile')
    
    tickets = request.user.client.ticket_set.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 20)  # 20 tickets par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'tickets': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'queue_system/profile_activity.html', context)


@login_required
def delete_account(request):
    """
    Vue pour supprimer le compte utilisateur
    """
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if not password:
            messages.error(request, 'Mot de passe requis pour supprimer le compte.')
            return redirect('queue_system:profile')
        
        if not request.user.check_password(password):
            messages.error(request, 'Mot de passe incorrect.')
            return redirect('queue_system:profile')
        
        # Supprimer le compte
        user = request.user
        user.delete()
        
        messages.success(request, 'Compte supprimé avec succès.')
        return redirect('queue_system:home')
    
    return render(request, 'queue_system/delete_account.html')


@login_required
def admin_user_profile(request, user_id):
    """
    Vue pour que les admins puissent voir/modifier les profils d'autres utilisateurs
    """
    if request.user.role != 'admin':
        messages.error(request, 'Accès non autorisé.')
        return redirect('queue_system:home')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Logique de mise à jour par l'admin
        pass
    
    context = {
        'target_user': target_user,
        'user': request.user,
    }
    
    return render(request, 'queue_system/admin_user_profile.html', context)


# Décorateur personnalisé pour vérifier les permissions
def role_required(roles):
    """
    Décorateur pour vérifier les rôles utilisateur
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('queue_system:login')
            
            if request.user.role not in roles:
                messages.error(request, 'Accès non autorisé.')
                return redirect('queue_system:home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# -----------------------------------------------------------------
#  DASHBOARD ADMINISTRATEUR
# -----------------------------------------------------------------
@login_required
@role_required(['admin'])
def admin_dashboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    users = User.objects.all().select_related()
    tickets = Ticket.objects.all()
    services = Service.objects.all()

    stats = {
        'total_users': users.count(),
        'total_clients': users.filter(role='client').count(),
        'total_employees': users.filter(role='employee').count(),
        'total_tickets': tickets.count(),
        'completed_tickets': tickets.filter(status='completed').count(),
        'active_services': services.filter(is_active=True).count(),
    }

    return render(request, 'queue_system/admin_dashboard.html', {
        'stats': stats,
        'users': users[:10],  # exemple: afficher les 10 derniers
        'tickets': tickets.order_by('-created_at')[:10],
        'services': services,
    })
