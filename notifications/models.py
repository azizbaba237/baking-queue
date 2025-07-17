from django.db import models
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push'),
        ('display', 'Affichage'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']