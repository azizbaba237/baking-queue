from .models import Ticket

def get_ticket_position(ticket):
    """
    Retourne la position du ticket dans la file d’attente (1 = premier).
    """
    waiting_tickets = Ticket.objects.filter(
        service=ticket.service,
        status='waiting',
        created_at__lt=ticket.created_at
    ).count()

    return waiting_tickets + 1


def get_progress_percent(ticket):
    """
    Calcule un pourcentage de progression estimé pour la file d’attente.
    """
    position = get_ticket_position(ticket)
    total_waiting = Ticket.objects.filter(
        service=ticket.service,
        status='waiting'
    ).count()

    if total_waiting == 0:
        return 100  # Tous les tickets sont passés

    progress = max(0, min(100, int((1 - (position - 1) / total_waiting) * 100)))
    return progress
