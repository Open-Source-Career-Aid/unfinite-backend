# Generated by Django 4.1.5 on 2023-03-17 19:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_completion_track'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unfiniteuser',
            name='in_progress',
        ),
    ]