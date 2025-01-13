from django.urls import path

from . import views

urlpatterns = [
    path("validate/", views.validate_iban, name="iban-validate"),
    path("<str:iban>/", views.detail, name="account-detail"),
]
