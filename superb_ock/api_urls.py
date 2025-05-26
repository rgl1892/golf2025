from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'scores', api_views.ScoreViewSet)
router.register(r'rounds', api_views.RoundViewSet)
router.register(r'players', api_views.PlayerViewSet)
router.register(r'courses', api_views.CourseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('heatmap-data/', api_views.heatmap_data, name='api_heatmap_data'),
    path('round/<int:round_id>/scores/', api_views.round_scores, name='api_round_scores'),
]

