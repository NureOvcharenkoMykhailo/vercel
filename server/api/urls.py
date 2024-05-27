from django.urls import path

from .views import *

urlpatterns = [
    *AccountView.get_url_patterns(),
    *FoodView.get_url_patterns(),
    *SubmissionView.get_url_patterns(),
    *DietView.get_url_patterns(),
    *MealPlanView.get_url_patterns(),
    *SystemView.get_url_patterns(),
    *IotView.get_url_patterns(),
]
