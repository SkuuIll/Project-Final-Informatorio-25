from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_post')
    list_filter = ('can_post',)
    search_fields = ('user__username',)
    actions = ['approve_posting']

    def approve_posting(self, request, queryset):
        queryset.update(can_post=True)
    approve_posting.short_description = "Aprobar usuarios seleccionados para postear"
