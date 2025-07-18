from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Notification

# Define un inline para el modelo Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('avatar', 'bio', 'can_post')

# Define un nuevo UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_can_post')
    list_select_related = ('profile',)

    def get_can_post(self, instance):
        return instance.profile.can_post
    get_can_post.short_description = 'Puede postear'
    get_can_post.boolean = True

# Re-registra el User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registra el modelo Notification
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'message')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_post')
    list_filter = ('can_post',)
    search_fields = ('user__username',)
    actions = ['approve_posting']

    def approve_posting(self, request, queryset):
        queryset.update(can_post=True)
    approve_posting.short_description = "Aprobar usuarios seleccionados para postear"
