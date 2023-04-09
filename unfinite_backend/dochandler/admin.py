from django.contrib import admin
from .models import Document

# Register your models here.
@admin.register(Document)
class Document(admin.ModelAdmin):
    list_display = ('url', 'num_pages', 'created', 'user',)