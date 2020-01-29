from django.contrib import admin
from .models import Poll, Choice, UserChoice


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_filter = ("channel", "anonymous")
    readonly_fields = ["created_at"]


admin.site.register(Choice)
admin.site.register(UserChoice)
