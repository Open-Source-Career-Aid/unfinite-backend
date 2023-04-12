from django.contrib import admin
from .models import Document, Thread, QA, FeedbackModel

# Register your models here.
@admin.register(Document)
class Document(admin.ModelAdmin):
    list_display = ('url', 'num_pages', 'created', 'user',)

@admin.register(Thread)
class Thread(admin.ModelAdmin):
    list_display = ('id', 'qamodels', 'promptmessages', 'created', 'updated',)

@admin.register(QA)
class QA(admin.ModelAdmin):
    list_display = ('question', 'answer', 'created', 'feedback',)