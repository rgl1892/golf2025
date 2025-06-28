from django.core.management.base import BaseCommand
from django.core.files import File
from superb_ock.models import CarouselImage
import os

class Command(BaseCommand):
    help = 'Set up initial carousel images'

    def handle(self, *args, **options):
        # Clear existing carousel images
        CarouselImage.objects.all().delete()
        
        # Create initial carousel images
        carousel_data = [
            {
                'title': 'The Superb Ock Golf Experience',
                'description': 'Memorable moments from our golf tournaments around the world.',
                'filename': 'carousel1.jpg',
                'order': 1
            },
            {
                'title': 'Championship Golf',
                'description': 'Competing on world-class courses with friends.',
                'filename': 'carousel2.jpg',
                'order': 2
            },
            {
                'title': 'Global Adventures',
                'description': 'From Portugal to Morocco to Turkey - golf adventures continue.',
                'filename': 'carousel3.jpg',
                'order': 3
            }
        ]
        
        for data in carousel_data:
            image_path = f"/Users/richardlongdon/Documents/GitHub/golf2025/media/carousel/{data['filename']}"
            
            if os.path.exists(image_path):
                carousel_image = CarouselImage(
                    title=data['title'],
                    description=data['description'],
                    order=data['order'],
                    is_active=True
                )
                
                with open(image_path, 'rb') as f:
                    carousel_image.image.save(
                        data['filename'],
                        File(f),
                        save=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created carousel image: {data["title"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Image file not found: {image_path}')
                )