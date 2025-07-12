import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from superb_ock.models import Highlight, Score


class Command(BaseCommand):
    help = 'Load highlights from CSV files and link them to scores'

    def handle(self, *args, **options):
        self.stdout.write('Starting highlights import...')
        
        # Clear existing highlights
        self.stdout.write('Clearing existing highlights...')
        Highlight.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Existing highlights cleared.'))
        
        # Load highlights from CSV
        highlights_csv = os.path.join(settings.BASE_DIR, 'highlights.csv')
        highlight_link_csv = os.path.join(settings.BASE_DIR, 'highlight_link.csv')
        
        # Dictionary to map CSV IDs to Highlight instances
        highlight_map = {}
        
        # Read highlights.csv and create Highlight objects
        self.stdout.write('Loading highlights from CSV...')
        with open(highlights_csv, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                csv_id = int(row['id'])
                filename = row['video_filename']
                
                # Derive title from filename
                title = self.derive_title_from_filename(filename)
                
                # Create highlight with specific ID from CSV
                highlight = Highlight(
                    id=csv_id,
                    title=title,
                    video=f'highlights/{filename}'
                )
                highlight.save()
                
                highlight_map[csv_id] = highlight
                self.stdout.write(f'Created highlight: {title}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(highlight_map)} highlights.'))
        
        # Read highlight_link.csv and link highlights to scores
        self.stdout.write('Linking highlights to scores...')
        links_created = 0
        
        with open(highlight_link_csv, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                score_id = int(row['score_id'])
                video_id = int(row['video_id'])
                
                try:
                    score = Score.objects.get(id=score_id)
                    highlight = highlight_map.get(video_id)
                    
                    if highlight:
                        score.highlight.add(highlight)
                        links_created += 1
                        self.stdout.write(f'Linked highlight "{highlight.title}" to score {score_id}')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Highlight with video_id {video_id} not found')
                        )
                        
                except Score.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Score with id {score_id} not found')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed! Created {len(highlight_map)} highlights and {links_created} score links.'
            )
        )
    
    def derive_title_from_filename(self, filename):
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Replace underscores and hyphens with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Handle special cases
        name = name.replace('WhatsApp Video', 'WhatsApp Video')
        name = name.replace('IMG ', 'IMG ')
        
        # Title case
        return name.title()