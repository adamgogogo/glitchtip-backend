# Generated by Django 3.0.8 on 2020-08-04 00:53

from django.db import migrations
from .sql.add_event_tags_function import ADD_EVENT_TAGS


class Migration(migrations.Migration):

    dependencies = [
        ("issues", "0003_auto_20200731_1531"),
    ]

    operations = [
        migrations.RunSQL(
            sql=ADD_EVENT_TAGS, reverse_sql="DROP FUNCTION IF EXISTS add_event_tags;",
        ),
    ]