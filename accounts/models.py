from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=80)
    country = models.CharField(max_length=2, default="DE")
    risk_class = models.PositiveSmallIntegerField(default=1)
    failed_logins = models.PositiveIntegerField(default=0)
    created_on = models.DateField()

    def __str__(self):
        return self.name


class Account(models.Model):
    ACTIVE, FROZEN, CLOSED = "active", "frozen", "closed"
    STATUSES = [(ACTIVE, "Active"), (FROZEN, "Frozen"), (CLOSED, "Closed")]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="accounts")
    iban = models.CharField(max_length=34, unique=True)
    currency = models.CharField(max_length=3, default="EUR")
    balance_minor = models.BigIntegerField(default=0)
    opened_on = models.DateField()
    last_activity_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUSES, default=ACTIVE)

    def __str__(self):
        return self.iban
