# Generated by Django 4.1.5 on 2023-03-04 17:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_query_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created', models.DateField()),
                ('updated', models.DateField()),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.query')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SERPFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.CharField(choices=[('TU', 'Thumbs-up'), ('TD', 'Thumbds-down'), ('TN', 'Neutral')], default='TN', max_length=2)),
                ('created', models.DateField()),
                ('updated', models.DateField()),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.query')),
                ('serp', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.serp')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Feedback',
        ),
    ]
