from django.db import models

from accounts.models import Account


class JournalEntry(models.Model):
    ref = models.CharField(max_length=24, unique=True)
    booked_on = models.DateField()
    kind = models.CharField(max_length=12, default="transfer")
    memo = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["booked_on", "id"]

    def __str__(self):
        return self.ref


class Posting(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="postings")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="postings")
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)

    class Meta:
        ordering = ["entry__booked_on", "id"]
