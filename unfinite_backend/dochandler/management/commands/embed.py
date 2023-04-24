# embeds the given document
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from dochandler.models import Document
from django.conf import settings
import pandas, pinecone

pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

class Command(BaseCommand):
    def handle(self, **options):
        doc_id = int(input("Document ID:\n-> "))
        d = Document.objects.get(id=doc_id)
        d.embed(index)
