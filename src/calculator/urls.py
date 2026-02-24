from django.urls import path
from . import views

urlpatterns = [
    path('', views.calculator, name='calculator'),
    path('results/', views.results, name='results')
]
