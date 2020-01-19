# Generated by Django 3.0.1 on 2020-01-19 15:17

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0003_auto_20200114_0156'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='context',
        ),
        migrations.RemoveField(
            model_name='event',
            name='contexts',
        ),
        migrations.RemoveField(
            model_name='event',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='event',
            name='culprit',
        ),
        migrations.RemoveField(
            model_name='event',
            name='entries',
        ),
        migrations.RemoveField(
            model_name='event',
            name='errors',
        ),
        migrations.RemoveField(
            model_name='event',
            name='location',
        ),
        migrations.RemoveField(
            model_name='event',
            name='message',
        ),
        migrations.RemoveField(
            model_name='event',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='event',
            name='packages',
        ),
        migrations.RemoveField(
            model_name='event',
            name='platform',
        ),
        migrations.RemoveField(
            model_name='event',
            name='sdk',
        ),
        migrations.RemoveField(
            model_name='event',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='event',
            name='title',
        ),
        migrations.RemoveField(
            model_name='event',
            name='user',
        ),
        migrations.AddField(
            model_name='event',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
            preserve_default=False,
        ),
    ]
