# Generated by Django 3.0 on 2019-12-05 03:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0002_auto_20191204_1456'),
    ]

    operations = [
        migrations.RenameField(
            model_name='issue',
            old_name='event_type',
            new_name='type',
        ),
    ]
