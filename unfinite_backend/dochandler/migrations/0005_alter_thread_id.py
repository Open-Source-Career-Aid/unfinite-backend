# Generated by Django 4.1.5 on 2023-04-15 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dochandler', '0004_rename_document_pages_document_document_chunks_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='id',
            field=models.TextField(default='9a293f61b2f5403f', editable=False, primary_key=True, serialize=False),
        ),
    ]
