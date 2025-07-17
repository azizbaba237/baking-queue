from django.contrib import admin
from .models import *
from accounts.models import *

# Register your models here.
admin.site.register(Service)
admin.site.register(Counter)
admin.site.register(Ticket)
admin.site.register(Queue)
admin.site.register(Evaluation)
admin.site.register(User)
admin.site.register(Client)
admin.site.register(Employee)

    
