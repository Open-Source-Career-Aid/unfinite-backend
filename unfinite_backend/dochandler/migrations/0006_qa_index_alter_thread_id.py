# Generated by Django 4.1.5 on 2023-04-15 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dochandler', '0005_alter_thread_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='qa',
            name='index',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='thread',
            name='id',
            field=models.TextField(default='5ee212c357094fb4', editable=False, primary_key=True, serialize=False),
        ),
    ]