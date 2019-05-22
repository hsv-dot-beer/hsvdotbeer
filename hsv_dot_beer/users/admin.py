from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from beers.admin import UserFavoriteBeerInline
from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    inlines = [UserFavoriteBeerInline]
