from django.contrib import admin
from .models import Document, Thread, QA, FeedbackModel, QuestionEventLog

# Register your models here.
@admin.register(Document)
class Document(admin.ModelAdmin):
    list_display = ('url', 'num_chunks', 'created', 'user', 'title')

@admin.register(Thread)
class Thread(admin.ModelAdmin):
    list_display = ('id', 'qamodels', 'promptmessages', 'created', 'updated',)

@admin.register(QA)
class QA(admin.ModelAdmin):
    list_display = ('question', 'answer', 'created', 'feedback', 'txttosummarize')

@admin.register(QuestionEventLog)
class QuestionEventLog(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'event_message', 'event_time')