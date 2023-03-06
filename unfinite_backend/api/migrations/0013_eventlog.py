# Generated by Django 4.1.5 on 2023-03-06 18:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_completion_query_alter_completion_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_was_new', models.BooleanField(null=True)),
                ('serp_was_new', models.BooleanField(null=True)),
                ('completion_idx', models.IntegerField(blank=True, null=True)),
                ('desc', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('completion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.completion')),
                ('query', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.query')),
                ('serp', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.serp')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]