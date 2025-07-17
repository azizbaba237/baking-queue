from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # App principale
    path('', include('queue_system.urls', namespace='queue_system')),

    # Gestion des comptes
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Notifications
    # path('notifications/', include('notification.urls', namespace='notification')),

    # # Statistiques
    # path('statistics/', include('statistic.urls', namespace='statistic')),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
