from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('admin/', admin.site.urls),
]
