# Generated by Django 4.1.5 on 2023-03-05 01:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_rename_queryfeedback_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='query',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='api.query'),
        ),
    ]
