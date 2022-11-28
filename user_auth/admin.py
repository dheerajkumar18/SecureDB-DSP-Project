from django.contrib import admin
from user_auth.models import User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('first_name', 'last_name', 'email')


admin.site.register(User, UserAdmin)
