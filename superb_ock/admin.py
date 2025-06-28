from django.contrib import admin
from django.utils.html import format_html
from .models import *

# Customize admin site header
admin.site.site_header = "The Superb Ock Golf Admin"
admin.site.site_title = "Golf Admin"
admin.site.index_title = "Golf Tournament Management"

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
    list_display = ['player_name', 'round_info', 'hole_info', 'shots_taken', 'stableford', 'handicap_display']
    list_editable = ['shots_taken', 'stableford']
    list_filter = ['golf_round__event', 'hole__golf_course', 'sandy']
    search_fields = ['player__first_name', 'player__second_name', 'hole__golf_course__name']
    ordering = ['-golf_round__id', 'hole__hole_number']
    
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
            'description': 'Special achievements on this hole'
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

@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['title', 'has_video', 'has_thumbnail']
    search_fields = ['title']
    ordering = ['title']
    
    fieldsets = (
        ('Highlight Information', {
            'fields': ('title', 'video', 'thumbnail'),
            'description': 'Golf highlight videos and thumbnails'
        }),
    )
    
    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True
    has_video.short_description = "Video"
    
    def has_thumbnail(self, obj):
        return bool(obj.thumbnail)
    has_thumbnail.boolean = True
    has_thumbnail.short_description = "Thumbnail"
 