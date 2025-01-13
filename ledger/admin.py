from django.contrib import admin

from .models import JournalEntry, Posting


class PostingInline(admin.TabularInline):
    model = Posting
    extra = 0


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("ref", "booked_on", "kind")
    inlines = [PostingInline]
