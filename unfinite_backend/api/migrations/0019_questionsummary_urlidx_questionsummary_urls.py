# Generated by Django 4.1.5 on 2023-03-22 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_relevantquestions_questionsummary'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionsummary',
            name='urlidx',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='questionsummary',
            name='urls',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
