import os
from django.core.management.base import BaseCommand
from django.conf import settings
from superb_ock.models import Highlight
from superb_ock.services import VideoThumbnailGenerator


class Command(BaseCommand):
    help = 'Generate thumbnails and preview images for highlight videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )

    def handle(self, *_args, **options):
        self.stdout.write('Starting thumbnail generation...')

        highlights = Highlight.objects.all()
        generator = VideoThumbnailGenerator()

        success_count = 0
        skip_count = 0
        error_count = 0

        for highlight in highlights:
            self.stdout.write(f'Processing: {highlight.title}')

            # Skip if thumbnail exists and not regenerating
            if highlight.thumbnail and not options['regenerate']:
                self.stdout.write(f'  Thumbnail exists, skipping...')
                skip_count += 1
                continue

            video_path = os.path.join(settings.MEDIA_ROOT, str(highlight.video))

            if not os.path.exists(video_path):
                self.stdout.write(
                    self.style.WARNING(f'  Video file not found: {video_path}')
                )
                error_count += 1
                continue

            try:
                # Generate thumbnail and preview images using service
                success = generator.generate_thumbnails_and_previews(highlight)

                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Generated images for {highlight.title}')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  Failed to generate images for {highlight.title}')
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing {highlight.title}: {str(e)}')
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nThumbnail generation completed!\n'
                f'  Success: {success_count}\n'
                f'  Skipped: {skip_count}\n'
                f'  Errors: {error_count}'
            )
        )