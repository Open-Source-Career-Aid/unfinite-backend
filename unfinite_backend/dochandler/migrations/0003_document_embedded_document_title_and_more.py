# Generated by Django 4.1.5 on 2023-04-18 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dochandler', '0002_alter_thread_id_questioneventlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='embedded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='document',
            name='title',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='document_chunks',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='num_chunks',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='thread',
            name='id',
            field=models.CharField(default='862b68f7cfe24606', editable=False, max_length=16, primary_key=True, serialize=False),
        ),
    ]
