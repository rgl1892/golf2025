import cv2
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image, ImageEnhance, ImageFilter
import io
from superb_ock.models import Highlight, HighlightPreview


class Command(BaseCommand):
    help = 'Generate thumbnails and preview images for highlight videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting thumbnail generation...')
        
        highlights = Highlight.objects.all()
        
        for highlight in highlights:
            self.stdout.write(f'Processing: {highlight.title}')
            
            # Skip if thumbnail exists and not regenerating
            if highlight.thumbnail and not options['regenerate']:
                self.stdout.write(f'  Thumbnail exists, skipping...')
                continue
            
            video_path = os.path.join(settings.MEDIA_ROOT, str(highlight.video))
            
            if not os.path.exists(video_path):
                self.stdout.write(
                    self.style.WARNING(f'  Video file not found: {video_path}')
                )
                continue
            
            try:
                # Generate thumbnail and preview images
                self.generate_images_for_highlight(highlight, video_path)
                self.stdout.write(
                    self.style.SUCCESS(f'  Generated images for {highlight.title}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing {highlight.title}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('Thumbnail generation completed!'))

    def generate_images_for_highlight(self, highlight, video_path):
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open video file: {video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        if duration == 0:
            raise Exception("Cannot determine video duration")
        
        # Generate thumbnail (middle frame)
        thumbnail_timestamp = duration / 2
        self.generate_thumbnail(cap, highlight, thumbnail_timestamp, fps)
        
        # Generate 3 preview images at 25%, 50%, 75% of video
        preview_timestamps = [duration * 0.25, duration * 0.5, duration * 0.75]
        
        # Clear existing previews if regenerating
        if hasattr(highlight, 'previews'):
            highlight.previews.all().delete()
        
        for i, timestamp in enumerate(preview_timestamps):
            self.generate_preview(cap, highlight, timestamp, fps, i)
        
        cap.release()

    def generate_thumbnail(self, cap, highlight, timestamp, fps):
        # Seek to timestamp
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if not ret:
            raise Exception("Cannot read frame for thumbnail")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Enhance image quality
        pil_image = self.enhance_image(pil_image)
        
        # Resize to high-quality thumbnail size (HD-ready)
        pil_image.thumbnail((800, 600), Image.Resampling.LANCZOS)
        
        # Save to BytesIO with high quality
        img_io = io.BytesIO()
        pil_image.save(img_io, format='JPEG', quality=95, optimize=True)
        img_io.seek(0)
        
        # Save to model
        filename = f'{highlight.id}_thumbnail.jpg'
        highlight.thumbnail.save(
            filename,
            ContentFile(img_io.getvalue()),
            save=True
        )

    def generate_preview(self, cap, highlight, timestamp, fps, order):
        # Seek to timestamp
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if not ret:
            raise Exception(f"Cannot read frame for preview {order}")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Enhance image quality
        pil_image = self.enhance_image(pil_image)
        
        # Resize to high-quality preview size (HD-ready)
        pil_image.thumbnail((600, 400), Image.Resampling.LANCZOS)
        
        # Save to BytesIO with high quality
        img_io = io.BytesIO()
        pil_image.save(img_io, format='JPEG', quality=95, optimize=True)
        img_io.seek(0)
        
        # Create HighlightPreview
        preview = HighlightPreview.objects.create(
            highlight=highlight,
            timestamp=timestamp,
            order=order
        )
        
        filename = f'{highlight.id}_preview_{order}.jpg'
        preview.image.save(
            filename,
            ContentFile(img_io.getvalue()),
            save=True
        )
    
    def enhance_image(self, image):
        """Enhance image quality with sharpening and color adjustment"""
        try:
            # Apply subtle sharpening
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            # Enhance color saturation slightly
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Image enhancement failed: {str(e)}')
            )
            return image  # Return original if enhancement fails