# Generated by Django 5.1.7 on 2025-03-25 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superb_ock', '0010_player_handedness'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='info',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='player',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='player',
            name='slug',
            field=models.SlugField(default=''),
        ),
    ]
