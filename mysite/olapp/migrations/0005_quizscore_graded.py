# Generated by Django 4.2.1 on 2023-07-23 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olapp', '0004_courseenrolment'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizscore',
            name='graded',
            field=models.BooleanField(default=False),
        ),
    ]
