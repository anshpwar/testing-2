from django.contrib import admin

from .models import Account, Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "risk_class")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("iban", "currency", "balance_minor", "status")
    list_filter = ("status", "currency")
