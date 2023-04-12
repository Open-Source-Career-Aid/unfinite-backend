# Generated by Django 4.1.7 on 2023-04-12 01:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dochandler', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('thumbs', models.IntegerField(default=0)),
                ('textfeedback', models.TextField(blank=True, default='', null=True)),
                ('created', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.TextField(default='24fc23d1a035438b', editable=False, primary_key=True, serialize=False)),
                ('qamodels', models.TextField(default='[]')),
                ('promptmessages', models.TextField(blank=True, default='[]', null=True)),
                ('created', models.DateTimeField()),
                ('updated', models.DateTimeField()),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='QA',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('docids', models.TextField()),
                ('created', models.DateTimeField()),
                ('feedback', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dochandler.feedbackmodel')),
                ('thread', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dochandler.thread')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
