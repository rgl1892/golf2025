"""
Media Processing Service

Centralizes video thumbnail generation and image enhancement logic.
Eliminates ~150 lines of duplicated code from admin.py and admin_views.py.

Usage:
    from superb_ock.services import VideoThumbnailGenerator

    generator = VideoThumbnailGenerator()
    generator.generate_thumbnails_and_previews(highlight, request)
"""

import os
import cv2
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
from django.core.files.base import ContentFile

from ..constants import MediaSettings
from ..logging_config import media_logger


class ImageProcessor:
    """
    Utility class for image enhancement operations.

    Provides consistent image quality improvements across the application.
    """

    @staticmethod
    def enhance_image(image):
        """
        Enhance image quality with filters and adjustments.

        Args:
            image: PIL Image object

        Returns:
            Enhanced PIL Image object
        """
        try:
            # Apply unsharp mask for sharpness
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)

            # Enhance color saturation
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)

            return image
        except Exception as e:
            media_logger.warning(f"Failed to enhance image: {e}")
            return image


class VideoThumbnailGenerator:
    """
    Service for generating thumbnails and preview images from video files.

    This service centralizes all video processing logic for creating:
    - Main thumbnail image (at video midpoint)
    - Preview images (at 25%, 50%, 75% positions)

    All images are enhanced for quality before saving.
    """

    def __init__(self):
        self.image_processor = ImageProcessor()

    def generate_thumbnails_and_previews(self, highlight, request=None):
        """
        Generate thumbnail and preview images for a highlight video.

        Args:
            highlight: Highlight model instance with video_file
            request: Optional Django request object for messages

        Returns:
            bool: True if successful, False otherwise
        """
        if not highlight.video_file:
            media_logger.warning(f"No video file for highlight {highlight.id}")
            return False

        video_path = highlight.video_file.path

        if not os.path.exists(video_path):
            media_logger.error(f"Video file not found: {video_path}")
            return False

        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                media_logger.error(f"Failed to open video: {video_path}")
                return False

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0 or fps == 0:
                media_logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
                cap.release()
                return False

            # Generate main thumbnail at midpoint
            midpoint = total_frames / 2
            self._generate_thumbnail(cap, highlight, midpoint, fps)
            media_logger.info(f"Generated thumbnail for highlight {highlight.id}")

            # Generate preview images
            for i, position in enumerate(MediaSettings.PREVIEW_POSITIONS):
                timestamp = total_frames * position
                self._generate_preview(cap, highlight, timestamp, fps, i + 1)

            media_logger.info(f"Generated {len(MediaSettings.PREVIEW_POSITIONS)} previews for highlight {highlight.id}")

            cap.release()
            return True

        except Exception as e:
            media_logger.error(f"Error generating thumbnails for highlight {highlight.id}: {e}")
            if 'cap' in locals():
                cap.release()
            return False

    def _generate_thumbnail(self, cap, highlight, timestamp, fps):
        """
        Generate main thumbnail image at specified timestamp.

        Args:
            cap: OpenCV VideoCapture object
            highlight: Highlight model instance
            timestamp: Frame number to capture
            fps: Video frames per second
        """
        # Set video position to timestamp
        cap.set(cv2.CAP_PROP_POS_FRAMES, timestamp)

        # Read the frame
        ret, frame = cap.read()

        if not ret:
            media_logger.warning(f"Failed to read frame at {timestamp} for highlight {highlight.id}")
            return

        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # Enhance image quality
        pil_image = self.image_processor.enhance_image(pil_image)

        # Save to BytesIO
        output = BytesIO()
        pil_image.save(output, format='JPEG', quality=MediaSettings.THUMBNAIL_QUALITY)
        output.seek(0)

        # Save to model
        filename = f"thumbnail_{highlight.id}.jpg"
        highlight.thumbnail.save(filename, ContentFile(output.read()), save=True)

        media_logger.debug(f"Saved thumbnail for highlight {highlight.id} at timestamp {timestamp}")

    def _generate_preview(self, cap, highlight, timestamp, fps, order):
        """
        Generate preview image at specified timestamp.

        Args:
            cap: OpenCV VideoCapture object
            highlight: Highlight model instance
            timestamp: Frame number to capture
            fps: Video frames per second
            order: Preview order number (1, 2, 3)
        """
        from ..models import HighlightPreview

        # Set video position to timestamp
        cap.set(cv2.CAP_PROP_POS_FRAMES, timestamp)

        # Read the frame
        ret, frame = cap.read()

        if not ret:
            media_logger.warning(f"Failed to read frame at {timestamp} for preview {order}")
            return

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # Enhance image quality
        pil_image = self.image_processor.enhance_image(pil_image)

        # Save to BytesIO
        output = BytesIO()
        pil_image.save(output, format='JPEG', quality=MediaSettings.THUMBNAIL_QUALITY)
        output.seek(0)

        # Create or update HighlightPreview
        preview, created = HighlightPreview.objects.get_or_create(
            highlight=highlight,
            order=order
        )

        filename = f"preview_{highlight.id}_{order}.jpg"
        preview.image.save(filename, ContentFile(output.read()), save=True)

        action = "Created" if created else "Updated"
        media_logger.debug(f"{action} preview {order} for highlight {highlight.id}")

    def generate_for_queryset(self, highlights, request=None):
        """
        Generate thumbnails and previews for multiple highlights.

        Args:
            highlights: QuerySet or list of Highlight objects
            request: Optional Django request object for messages

        Returns:
            dict: Statistics about generation (success_count, error_count)
        """
        stats = {'success_count': 0, 'error_count': 0}

        for highlight in highlights:
            if self.generate_thumbnails_and_previews(highlight, request):
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1

        media_logger.info(
            f"Batch thumbnail generation complete: "
            f"{stats['success_count']} successful, {stats['error_count']} errors"
        )

        return stats
