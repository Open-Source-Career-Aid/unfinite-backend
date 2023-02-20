from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *


@admin.register(UnfiniteUser)
class UserAdmin(DjangoUserAdmin):
    # since we made a child class of the Django AbstractUser, which we want to use as the 
    # default user object representation, add an admin page for it. Won't show up otherwise.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

# below, are the admin pages for other Models. TODO: make them more useful.

@admin.register(BetaKey)
class BetaKeyAdmin(admin.ModelAdmin):
    # TODO: allow upload of CSV with emails to generate keys with. See unfinite_backend/add_beta_keys.py
    # which does the same thing.
    list_display = ('user_email',)

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'num_tokens', 'num_searched')

@admin.register(SERP)
class SERPAdmin(admin.ModelAdmin):
    list_display = ('search_string',)