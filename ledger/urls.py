from django.urls import path

from . import views

urlpatterns = [
    path("post/", views.post, name="ledger-post"),
    path("trial/<str:currency>/", views.trial, name="ledger-trial"),
    path("<str:iban>/statement/", views.statement, name="ledger-statement"),
]
