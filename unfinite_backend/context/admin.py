from django.contrib import admin

# Register your models here.
from .models import Topic, Edge

class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'synonyms', 'docids']

class EdgeAdmin(admin.ModelAdmin):
    list_display = ['start_node', 'end_node', 'docid', 'weight']

admin.site.register(Topic)
admin.site.register(Edge)

