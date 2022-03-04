from django.urls import path
from . import views

urlpatterns = [
    path('interact/', views.interact)
]