"""
Management command to backup the database
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime
import subprocess
import os


class Command(BaseCommand):
    help = 'Backup database to JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output directory for backup file (default: project root)',
            default=str(settings.BASE_DIR)
        )

    def handle(self, *args, **options):
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = options['output']
        backup_file = os.path.join(output_dir, f'backup_{timestamp}.json')

        self.stdout.write(
            self.style.WARNING(f'Creating database backup...')
        )

        try:
            # Run dumpdata command
            result = subprocess.run([
                'python', 'manage.py', 'dumpdata',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--exclude', 'sessions',
                '--indent', '2',
                '--output', backup_file
            ], capture_output=True, text=True, check=True)

            # Check file size
            file_size = os.path.getsize(backup_file) / (1024 * 1024)  # Convert to MB

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Backup created successfully!'
                    f'\n  File: {backup_file}'
                    f'\n  Size: {file_size:.2f} MB'
                )
            )

            # Show backup stats
            self.stdout.write('\nBackup includes:')
            self.stdout.write('  - Golf rounds and scores')
            self.stdout.write('  - Players and events')
            self.stdout.write('  - Highlights and media references')
            self.stdout.write('  - User profiles and settings')

            self.stdout.write(
                self.style.WARNING(
                    '\nNote: Media files (videos, images) are NOT included.'
                    '\nBack up the media/ directory separately.'
                )
            )

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ Backup failed: {e.stderr}'
                )
            )
            return

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ Unexpected error: {str(e)}'
                )
            )
            return
