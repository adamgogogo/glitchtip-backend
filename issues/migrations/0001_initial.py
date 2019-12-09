# Generated by Django 3.0 on 2019-12-08 23:28

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0002_auto_20191204_2155'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=225)),
            ],
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('type', models.PositiveSmallIntegerField(choices=[(0, 'default'), (1, 'error'), (2, 'csp')], default=0)),
                ('culprit', models.CharField(blank=True, max_length=1024, null=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'unresolved'), (1, 'resolved'), (2, 'ignored')], default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('event_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('context', django.contrib.postgres.fields.jsonb.JSONField()),
                ('contexts', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('culprit', models.CharField(blank=True, max_length=1024)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('entries', django.contrib.postgres.fields.jsonb.JSONField()),
                ('errors', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list)),
                ('location', models.CharField(blank=True, max_length=1024, null=True)),
                ('message', models.CharField(blank=True, max_length=1024, null=True)),
                ('packages', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('platform', models.CharField(max_length=255)),
                ('sdk', django.contrib.postgres.fields.jsonb.JSONField()),
                ('title', models.CharField(max_length=255)),
                ('user', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('issue', models.ForeignKey(help_text='Sentry calls this a group', on_delete=django.db.models.deletion.CASCADE, to='issues.Issue')),
                ('tags', models.ManyToManyField(blank=True, to='issues.EventTag')),
            ],
        ),
    ]
