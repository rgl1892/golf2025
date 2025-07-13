from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm, CharField, FileField, ChoiceField
from .models import Score, Highlight, Player, GolfRound, Hole
import json
import cv2
import os
from PIL import Image, ImageEnhance, ImageFilter
from django.core.files.base import ContentFile
import io

@staff_member_required
def bulk_highlight_link(request):
    """Custom admin view for bulk linking highlights to scores"""
    
    # Get selected score IDs from session
    score_ids = request.session.get('bulk_score_ids', [])
    
    if request.method == 'POST':
        highlight_id = request.POST.get('highlight_id')
        
        if highlight_id and score_ids:
            try:
                highlight = Highlight.objects.get(id=highlight_id)
                scores = Score.objects.filter(id__in=score_ids)
                
                # Link highlight to all selected scores
                for score in scores:
                    score.highlight.add(highlight)
                
                messages.success(
                    request, 
                    f'Successfully linked "{highlight.title}" to {len(scores)} scores.'
                )
                
                # Clear session data
                request.session.pop('bulk_score_ids', None)
                
                return redirect('admin:superb_ock_score_changelist')
                
            except Highlight.DoesNotExist:
                messages.error(request, 'Selected highlight not found.')
        else:
            messages.error(request, 'Please select a highlight.')
    
    # Get the selected scores for display
    scores = Score.objects.filter(id__in=score_ids).select_related(
        'player', 'hole__golf_course', 'golf_round__event'
    ).order_by('player__first_name', 'hole__hole_number')
    
    # Get all available highlights
    highlights = Highlight.objects.all().order_by('title')
    
    context = {
        'title': 'Bulk Link Highlights to Scores',
        'scores': scores,
        'highlights': highlights,
        'scores_count': len(score_ids)
    }
    
    return render(request, 'admin/bulk_highlight_link.html', context)

@staff_member_required
def highlight_management(request):
    """Advanced highlight-score management interface"""
    
    # Get filter parameters
    round_id = request.GET.get('round')
    player_id = request.GET.get('player')
    highlight_id = request.GET.get('highlight')
    
    # Base queryset
    scores = Score.objects.select_related(
        'player', 'hole__golf_course', 'golf_round__event'
    ).prefetch_related('highlight')
    
    # Apply filters
    if round_id:
        scores = scores.filter(golf_round_id=round_id)
    if player_id:
        scores = scores.filter(player_id=player_id)
    
    # Order by round, then player, then hole
    scores = scores.order_by('-golf_round_id', 'player__first_name', 'hole__hole_number')
    
    # Get filter options
    rounds = GolfRound.objects.select_related('event').order_by('-id')[:20]
    players = Player.objects.order_by('first_name', 'second_name')
    highlights = Highlight.objects.all().order_by('title')
    
    # Group scores by round and player for better display
    grouped_scores = {}
    for score in scores:
        round_key = f"Round {score.golf_round.id} - {score.golf_round.event.name}"
        player_key = f"{score.player.first_name} {score.player.second_name}"
        
        if round_key not in grouped_scores:
            grouped_scores[round_key] = {}
        if player_key not in grouped_scores[round_key]:
            grouped_scores[round_key][player_key] = []
        
        grouped_scores[round_key][player_key].append(score)
    
    context = {
        'title': 'Highlight Management',
        'grouped_scores': grouped_scores,
        'rounds': rounds,
        'players': players,
        'highlights': highlights,
        'selected_round': round_id,
        'selected_player': player_id,
        'selected_highlight': highlight_id,
    }
    
    return render(request, 'admin/highlight_management.html', context)

@staff_member_required
@require_POST
@csrf_exempt
def ajax_toggle_highlight(request):
    """AJAX endpoint to toggle highlight-score relationships"""
    try:
        data = json.loads(request.body)
        score_id = data.get('score_id')
        highlight_id = data.get('highlight_id')
        action = data.get('action')  # 'add' or 'remove'
        
        score = Score.objects.get(id=score_id)
        highlight = Highlight.objects.get(id=highlight_id)
        
        if action == 'add':
            score.highlight.add(highlight)
            message = f'Added "{highlight.title}" to score'
        elif action == 'remove':
            score.highlight.remove(highlight)
            message = f'Removed "{highlight.title}" from score'
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'highlight_count': score.highlight.count()
        })
        
    except (Score.DoesNotExist, Highlight.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Score or highlight not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

class RoundHighlightForm(ModelForm):
    """Form for adding highlights with round context"""
    video_file = FileField(required=True, help_text="Upload golf highlight video")
    custom_filename = CharField(
        max_length=100,
        required=False,
        help_text="Optional: Custom filename (without extension)"
    )
    player = ChoiceField(required=True, help_text="Select the player for this highlight")
    hole_number = ChoiceField(required=True, help_text="Select the hole number")
    
    class Meta:
        model = Highlight
        fields = ['title']
    
    def __init__(self, *args, round_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if round_id:
            # Get players from this round
            round_players = Score.objects.filter(
                golf_round_id=round_id
            ).values_list('player_id', 'player__first_name', 'player__second_name').distinct()
            
            player_choices = [('', '--- Select Player ---')]
            for player_id, first_name, second_name in round_players:
                player_choices.append((player_id, f"{first_name} {second_name}"))
            
            self.fields['player'].choices = player_choices
            
            # Get holes from this round
            round_holes = Score.objects.filter(
                golf_round_id=round_id
            ).values_list('hole__hole_number', flat=True).distinct().order_by('hole__hole_number')
            
            hole_choices = [('', '--- Select Hole ---')]
            for hole_num in round_holes:
                hole_choices.append((hole_num, f"Hole {hole_num}"))
            
            self.fields['hole_number'].choices = hole_choices

@staff_member_required
def add_round_highlight(request, round_id):
    """Add highlight with round context"""
    round_obj = get_object_or_404(GolfRound, id=round_id)
    
    if request.method == 'POST':
        form = RoundHighlightForm(request.POST, request.FILES, round_id=round_id)
        
        if form.is_valid():
            try:
                # Create the highlight
                highlight = Highlight()
                highlight.title = form.cleaned_data['title']
                
                # Handle video file
                video_file = form.cleaned_data['video_file']
                custom_filename = form.cleaned_data.get('custom_filename')
                
                if custom_filename:
                    # Use custom filename
                    extension = os.path.splitext(video_file.name)[1]
                    filename = f"highlights/{custom_filename}{extension}"
                else:
                    # Use original filename
                    filename = f"highlights/{video_file.name}"
                
                highlight.video.save(filename, video_file, save=False)
                highlight.save()
                
                # Generate thumbnails and previews
                generate_thumbnails_for_highlight(highlight)
                
                # Link to specific score if player and hole selected
                player_id = form.cleaned_data.get('player')
                hole_number = form.cleaned_data.get('hole_number')
                
                if player_id and hole_number:
                    try:
                        score = Score.objects.get(
                            golf_round_id=round_id,
                            player_id=player_id,
                            hole__hole_number=hole_number
                        )
                        score.highlight.add(highlight)
                        
                        messages.success(
                            request,
                            f'Highlight "{highlight.title}" created and linked to {score.player.first_name} {score.player.second_name} on Hole {hole_number}!'
                        )
                    except Score.DoesNotExist:
                        messages.warning(
                            request,
                            f'Highlight "{highlight.title}" created but could not find score for selected player/hole combination.'
                        )
                else:
                    messages.success(
                        request,
                        f'Highlight "{highlight.title}" created successfully! You can link it to scores in the admin.'
                    )
                
                return redirect('golf_round', round_id=round_id)
                
            except Exception as e:
                messages.error(request, f'Error creating highlight: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoundHighlightForm(round_id=round_id)
    
    # Get round context for display
    round_scores = Score.objects.filter(golf_round_id=round_id).select_related(
        'player', 'hole__golf_course'
    ).order_by('player__first_name', 'hole__hole_number')
    
    # Group by player for better display
    players_scores = {}
    for score in round_scores:
        player_name = f"{score.player.first_name} {score.player.second_name}"
        if player_name not in players_scores:
            players_scores[player_name] = []
        players_scores[player_name].append(score)
    
    context = {
        'title': f'Add Highlight - Round {round_id}',
        'form': form,
        'round_obj': round_obj,
        'round_id': round_id,
        'players_scores': players_scores,
    }
    
    return render(request, 'admin/add_round_highlight.html', context)

def generate_thumbnails_for_highlight(highlight):
    """Generate thumbnails and preview images for a highlight"""
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
        generate_thumbnail_for_highlight(cap, highlight, thumbnail_timestamp, fps)
        
        # Generate 3 preview images at 25%, 50%, 75% of video
        preview_timestamps = [duration * 0.25, duration * 0.5, duration * 0.75]
        
        # Clear existing previews
        highlight.previews.all().delete()
        
        for i, timestamp in enumerate(preview_timestamps):
            generate_preview_for_highlight(cap, highlight, timestamp, fps, i)
            
    finally:
        cap.release()

def generate_thumbnail_for_highlight(cap, highlight, timestamp, fps):
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
    pil_image = enhance_image(pil_image)
    
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

def generate_preview_for_highlight(cap, highlight, timestamp, fps, order):
    """Generate preview image"""
    from .models import HighlightPreview
    
    frame_number = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    ret, frame = cap.read()
    if not ret:
        raise Exception(f"Cannot read frame for preview {order}")
    
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Convert to PIL Image and enhance
    pil_image = Image.fromarray(frame_rgb)
    pil_image = enhance_image(pil_image)
    
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

def enhance_image(image):
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