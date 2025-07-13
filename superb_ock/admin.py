from django.contrib import admin
from django.utils.html import format_html
from django.forms import ModelForm, CharField
from django.core.files.storage import default_storage
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
import os
import cv2
from PIL import Image, ImageEnhance, ImageFilter
from django.core.files.base import ContentFile
import io
from .models import *

# Customize admin site header
admin.site.site_header = "The Superb Ock Golf Admin"
admin.site.site_title = "Golf Admin"
admin.site.index_title = "Golf Tournament Management"

# Custom filters
class HasVideoFilter(SimpleListFilter):
    title = 'has video'
    parameter_name = 'has_video'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Video'),
            ('no', 'No Video'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(video='')
        if self.value() == 'no':
            return queryset.filter(video='')
        return queryset

class HasHighlightFilter(SimpleListFilter):
    title = 'has highlights'
    parameter_name = 'has_highlights'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Highlights'),
            ('no', 'No Highlights'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(highlight__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(highlight__isnull=True)
        return queryset

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'focal_display', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image')
        }),
        ('Image Positioning', {
            'fields': ('focal_point_x', 'focal_point_y'),
            'description': 'Adjust where the image is centered. 50,50 = center. 0,0 = top-left. 100,100 = bottom-right.'
        }),
        ('Display Options', {
            'fields': ('order', 'is_active'),
            'description': 'Control how and when this image appears in the carousel'
        }),
    )
    
    def focal_display(self, obj):
        return f"{obj.focal_point_x},{obj.focal_point_y}"
    focal_display.short_description = "Focal Point"
    
    class Media:
        css = {
            'all': ('admin/css/carousel_admin.css',)
        }
        js = ('admin/js/carousel_admin.js',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'handedness', 'ocks', 'rounds_played']
    list_editable = ['ocks']
    list_filter = ['handedness']
    search_fields = ['first_name', 'second_name']
    ordering = ['first_name', 'second_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'second_name', 'handedness', 'picture')
        }),
        ('Golf Stats', {
            'fields': ('ocks', 'info'),
            'description': 'Golf-related information and statistics'
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.second_name}"
    full_name.short_description = "Name"
    
    def rounds_played(self, obj):
        return Score.objects.filter(player=obj).values('golf_round').distinct().count()
    rounds_played.short_description = "Rounds"

@admin.register(GolfCourse)
class GolfCourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'tees', 'par', 'course_rating', 'slope_rating', 'holes_count']
    list_filter = ['country', 'tees']
    search_fields = ['name', 'country']
    ordering = ['name']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('name', 'country', 'tees', 'par')
        }),
        ('Difficulty Ratings', {
            'fields': ('course_rating', 'slope_rating'),
            'description': 'Official course difficulty ratings'
        }),
    )
    
    def holes_count(self, obj):
        return Hole.objects.filter(golf_course=obj).count()
    holes_count.short_description = "Holes"

@admin.register(Hole)
class HoleAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'hole_number', 'par', 'yards', 'stroke_index']
    list_editable = ['par', 'yards', 'stroke_index']
    list_filter = ['golf_course', 'par', 'hole_number']
    search_fields = ['golf_course__name']
    ordering = ['golf_course', 'hole_number']
    
    fieldsets = (
        ('Hole Details', {
            'fields': ('golf_course', 'hole_number', 'par')
        }),
        ('Additional Info', {
            'fields': ('yards', 'stroke_index'),
            'description': 'Distance and difficulty ranking'
        }),
    )
    
    def course_name(self, obj):
        return f"{obj.golf_course.name} - Hole {obj.hole_number}"
    course_name.short_description = "Course & Hole"

@admin.register(GolfEvent)
class GolfEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'scoring', 'rounds_count', 'players_count']
    list_filter = ['scoring']
    search_fields = ['name']
    ordering = ['name']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'scoring'),
            'description': 'Tournament details and scoring format'
        }),
    )
    
    def rounds_count(self, obj):
        return GolfRound.objects.filter(event=obj).count()
    rounds_count.short_description = "Rounds"
    
    def players_count(self, obj):
        return Score.objects.filter(golf_round__event=obj).values('player').distinct().count()
    players_count.short_description = "Players"

@admin.register(GolfRound)
class GolfRoundAdmin(admin.ModelAdmin):
    list_display = ['round_id', 'event_name', 'date_display', 'players_count', 'scores_count']
    list_filter = ['event', 'date_started']
    search_fields = ['event__name']
    ordering = ['-date_started', '-id']
    # Removed date_hierarchy to avoid None date issues
    
    fieldsets = (
        ('Round Information', {
            'fields': ('event', 'date_started'),
            'description': 'When and where this round was played'
        }),
    )
    
    def round_id(self, obj):
        return f"Round {obj.id}"
    round_id.short_description = "Round"
    
    def event_name(self, obj):
        return obj.event.name
    event_name.short_description = "Event"
    
    def date_display(self, obj):
        if obj.date_started:
            return obj.date_started.strftime("%Y-%m-%d")
        return "No date set"
    date_display.short_description = "Date"
    
    def players_count(self, obj):
        return Score.objects.filter(golf_round=obj).values('player').distinct().count()
    players_count.short_description = "Players"
    
    def scores_count(self, obj):
        return Score.objects.filter(golf_round=obj).count()
    scores_count.short_description = "Scores"

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'round_info', 'hole_info', 'shots_taken', 'stableford', 'highlight_count', 'handicap_display']
    list_editable = ['shots_taken', 'stableford']
    list_filter = ['golf_round__event', 'hole__golf_course', 'sandy', HasHighlightFilter]
    search_fields = ['player__first_name', 'player__second_name', 'hole__golf_course__name']
    ordering = ['-golf_round__id', 'hole__hole_number']
    filter_horizontal = ['highlight']  # Makes it easier to select multiple highlights
    actions = ['bulk_link_highlight', 'bulk_unlink_highlights']
    
    fieldsets = (
        ('Score Information', {
            'fields': ('player', 'golf_round', 'hole', 'handicap_index')
        }),
        ('Performance', {
            'fields': ('shots_taken', 'stableford', 'sandy'),
            'description': 'Actual scoring performance'
        }),
        ('Highlights', {
            'fields': ('highlight',),
            'description': 'Link video highlights to this score. You can select multiple highlights.'
        }),
    )
    
    def player_name(self, obj):
        return f"{obj.player.first_name} {obj.player.second_name}"
    player_name.short_description = "Player"
    
    def round_info(self, obj):
        return f"R{obj.golf_round.id} - {obj.golf_round.event.name}"
    round_info.short_description = "Round"
    
    def hole_info(self, obj):
        return f"{obj.hole.golf_course.name} - Hole {obj.hole.hole_number}"
    hole_info.short_description = "Course & Hole"
    
    def handicap_display(self, obj):
        return f"{obj.handicap_index:.1f}"
    handicap_display.short_description = "HCP"
    
    def highlight_count(self, obj):
        count = obj.highlight.count()
        if count > 0:
            return f"🎬 {count}"
        return "-"
    highlight_count.short_description = "Highlights"
    
    def bulk_link_highlight(self, request, queryset):
        """Bulk action to link a highlight to multiple scores"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['bulk_score_ids'] = selected_ids
        
        return HttpResponseRedirect(reverse('admin:bulk_highlight_link'))
    bulk_link_highlight.short_description = "🎬 Link highlight to selected scores"
    
    def bulk_unlink_highlights(self, request, queryset):
        """Bulk action to remove all highlights from selected scores"""
        count = 0
        for score in queryset:
            if score.highlight.exists():
                score.highlight.clear()
                count += 1
        
        self.message_user(request, f"Removed highlights from {count} scores.")
    bulk_unlink_highlights.short_description = "🗑️ Remove all highlights from selected scores"

class HighlightAdminForm(ModelForm):
    custom_filename = CharField(
        max_length=100,
        required=False,
        help_text="Optional: Custom filename for the video (without extension). Leave blank to use uploaded filename."
    )
    
    class Meta:
        model = Highlight
        fields = '__all__'

@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    form = HighlightAdminForm
    list_display = ['title', 'has_video', 'has_thumbnail', 'preview_count', 'linked_scores', 'created_date']
    list_filter = [HasVideoFilter]
    search_fields = ['title']
    ordering = ['-id']
    readonly_fields = ['thumbnail_preview', 'video_preview', 'preview_images']
    
    fieldsets = (
        ('Video Upload', {
            'fields': ('title', 'video', 'custom_filename'),
            'description': 'Upload a new golf highlight video'
        }),
        ('Generated Content (Auto-generated)', {
            'fields': ('thumbnail', 'thumbnail_preview'),
            'description': 'Thumbnails are automatically generated when you save'
        }),
        ('Preview Images', {
            'fields': ('preview_images',),
            'description': 'Preview images for hover effects (auto-generated)'
        }),
        ('Video Preview', {
            'fields': ('video_preview',),
            'description': 'Embedded video player'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Handle custom filename
        if form.cleaned_data.get('custom_filename') and obj.video:
            custom_name = form.cleaned_data['custom_filename']
            # Get the file extension from the original video
            original_name = obj.video.name
            extension = os.path.splitext(original_name)[1]
            # Create new filename
            new_filename = f"highlights/{custom_name}{extension}"
            
            # Save with custom filename
            if not change:  # New object
                obj.video.name = new_filename
        
        super().save_model(request, obj, form, change)
        
        # Generate thumbnails and previews after saving
        if obj.video:
            try:
                self.generate_thumbnails_and_previews(obj, request)
                messages.success(request, f'Thumbnails and previews generated successfully for "{obj.title}"')
            except Exception as e:
                messages.error(request, f'Error generating thumbnails: {str(e)}')
    
    def generate_thumbnails_and_previews(self, highlight, request):
        """Generate thumbnails and preview images for the highlight"""
        video_path = highlight.video.path
        
        if not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open video file: {video_path}")
        
        try:
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
            
            # Clear existing previews
            highlight.previews.all().delete()
            
            for i, timestamp in enumerate(preview_timestamps):
                self.generate_preview(cap, highlight, timestamp, fps, i)
                
        finally:
            cap.release()
    
    def generate_thumbnail(self, cap, highlight, timestamp, fps):
        """Generate main thumbnail"""
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if not ret:
            raise Exception("Cannot read frame for thumbnail")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image and enhance
        pil_image = Image.fromarray(frame_rgb)
        pil_image = self.enhance_image(pil_image)
        
        # Resize to high-quality thumbnail size
        pil_image.thumbnail((800, 600), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
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
        """Generate preview image"""
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if not ret:
            raise Exception(f"Cannot read frame for preview {order}")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image and enhance
        pil_image = Image.fromarray(frame_rgb)
        pil_image = self.enhance_image(pil_image)
        
        # Resize to high-quality preview size
        pil_image.thumbnail((600, 400), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
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
        """Enhance image quality"""
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
        except Exception:
            return image  # Return original if enhancement fails
    
    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True
    has_video.short_description = "Video"
    
    def has_thumbnail(self, obj):
        return bool(obj.thumbnail)
    has_thumbnail.boolean = True
    has_thumbnail.short_description = "Thumbnail"
    
    def preview_count(self, obj):
        return obj.previews.count()
    preview_count.short_description = "Previews"
    
    def linked_scores(self, obj):
        count = obj.score_set.count()
        return f"{count} score{'s' if count != 1 else ''}"
    linked_scores.short_description = "Linked to"
    
    def created_date(self, obj):
        return obj.id  # Using ID as a proxy for creation order
    created_date.short_description = "ID"
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail Preview"
    
    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video controls style="max-width: 400px; max-height: 300px;"><source src="{}" type="video/mp4">Your browser does not support the video tag.</video>',
                obj.video.url
            )
        return "No video"
    video_preview.short_description = "Video Preview"
    
    def preview_images(self, obj):
        previews = obj.previews.all().order_by('order')
        if previews:
            html = '<div style="display: flex; gap: 10px;">'
            for preview in previews:
                html += format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 75px; border: 1px solid #ccc;" title="Preview {}"/>',
                    preview.image.url,
                    preview.order + 1
                )
            html += '</div>'
            return format_html(html)
        return "No preview images"
    preview_images.short_description = "Preview Images"

@admin.register(HighlightPreview)
class HighlightPreviewAdmin(admin.ModelAdmin):
    list_display = ['highlight_title', 'order', 'timestamp', 'image_preview']
    list_filter = ['highlight', 'order']
    ordering = ['highlight', 'order']
    readonly_fields = ['image_preview']
    
    def highlight_title(self, obj):
        return obj.highlight.title
    highlight_title.short_description = "Highlight"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"
 