from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('employee', 'Employee'),
        ('admin', 'Administrateur'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_vip = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_set",  # Nom unique
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",  # Nom unique
        related_query_name="user",
    )
    
    class Meta:
        db_table = 'custom_user'  # Nom de table personnalisé

    def __str__(self):
        return self.username
    
    
    
class Client(models.Model):
    CLIENT_TYPES = [
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('professional', 'Professionnel'),
        ('senior', 'Senior'),  
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES)
    birth_date = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Employee(models.Model):
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('busy', 'Occupé'),
        ('break', 'Pause'),
        ('offline', 'Hors ligne'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    hire_date = models.DateField()
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.employee_id}"
    

