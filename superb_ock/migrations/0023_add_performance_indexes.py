# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superb_ock', '0022_alter_userprofile_notifications_enabled'),
    ]

    operations = [
        # Add index to GolfRound.date_started for sorting recent rounds
        migrations.AlterField(
            model_name='golfround',
            name='date_started',
            field=models.DateField(blank=True, null=True, db_index=True),
        ),

        # Add indexes for Score queries (most commonly filtered fields)
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['golf_round', 'player'], name='score_round_player_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['player', '-golf_round'], name='score_player_round_idx'),
        ),

        # Add composite index for GolfRound queries (event + date)
        migrations.AddIndex(
            model_name='golfround',
            index=models.Index(fields=['event', '-date_started'], name='round_event_date_idx'),
        ),
    ]
