from django.db import models
from django.utils import timezone
from accounts.models import Client, Employee

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    estimated_duration = models.PositiveIntegerField(help_text="Durée en minutes")
    base_priority = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    
    def __str__(self):
        return self.name

class Counter(models.Model):
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('closed', 'Fermé'),
        ('maintenance', 'Maintenance'),
    ]
    
    name = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='closed')
    max_capacity = models.PositiveIntegerField(default=1)
    services = models.ManyToManyField(Service, related_name='counters')
    current_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('called', 'Appelé'),
        ('in_service', 'En service'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    ticket_number = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    priority = models.PositiveIntegerField(default=1)
    estimated_wait_time = models.PositiveIntegerField(default=0, help_text="Temps d'attente en minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    service_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    countdown_started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.service.name}"
    
    def get_position_in_queue(self):
        return Ticket.objects.filter(
            service=self.service,
            status='waiting',
            created_at__lt=self.created_at
        ).count() + 1
    
    def calculate_wait_time(self):
        waiting_tickets = Ticket.objects.filter(
            service=self.service,
            status='waiting',
            created_at__lt=self.created_at
        ).count()
        return waiting_tickets * self.service.estimated_duration
    
    def start_countdown(self):
        if not self.countdown_started_at:
            self.countdown_started_at = timezone.now()
            self.save(update_fields=['countdown_started_at'])
    
    def remaining_wait_time(self):
        if not self.countdown_started_at:
            return self.estimated_wait_time * 60  # en secondes
        elapsed = timezone.now() - self.countdown_started_at
        remaining = self.estimated_wait_time * 60 - int(elapsed.total_seconds())
        return max(0, remaining)

    def progress_percent(self):
        total = self.estimated_wait_time * 60
        remaining = self.remaining_wait_time()
        return min(100, int(100 * (1 - remaining / total))) if total > 0 else 0

class Queue(models.Model):
    service = models.OneToOneField(Service, on_delete=models.CASCADE)
    current_number = models.PositiveIntegerField(default=0)
    max_capacity = models.PositiveIntegerField(default=100)
    
    def get_next_ticket(self):
        return self.service.ticket_set.filter(status='waiting').first()
    
    def get_queue_length(self):
        return self.service.ticket_set.filter(status='waiting').count()

class Evaluation(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Évaluation {self.rating}/5 - Ticket {self.ticket.ticket_number}"
