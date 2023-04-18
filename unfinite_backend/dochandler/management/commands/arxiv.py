# this script takes a csv of arxiv papers, in the format returned by the arxivscraper
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from dochandler.models import Document
from django.conf import settings
import pandas, pinecone

pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

class Command(BaseCommand):
    def handle(self, **options):
        # now do the things that you want with your models here
        limit = 2

        csv_fname = input("Filename (with extension):\n-> ")
        df = pandas.read_csv(csv_fname)

        for row in df.head(limit).itertuples():
            try:
                Document.objects.get(url=row[10])
                print(f"'{row[3]}' already indexed")
            except Exception:
                print(f"indexing '{row[3]}'")
                d = Document.objects.create(url=row[10], title=row[3])
                d.save()
                d.scrape()
                d.embed(index)