from django.urls import path, include
from django.conf import settings

from . import views, admin_views, views_notifications
from .views import showcase, health

urlpatterns = [
    path("",views.Home.as_view() , name="home"),
    path("new_round",views.NewRound.as_view() , name="new_round"),
    path("rounds",views.RoundsOverview.as_view() , name="rounds_overview"),
    path("rounds/<int:round_id>",views.GolfRoundView.as_view() , name="golf_round"),
    path("rounds/<int:round_id>/<int:hole_number>",views.EditScore.as_view() , name="edit_score"),
    path("event/<int:event_id>",views.EventView.as_view(), name='event'),
    path("heatmap/",views.HeatMap.as_view() , name="heatmap"),
    path("highlights/",views.HighlightsView.as_view() , name="highlights"),

    # Monitoring
    path("health/", health.health_check, name="health_check"),

]
# Authentication
urlpatterns.extend(
    [
    path('login',views.logInUser,name='login'),
    path('logout',views.logOutUser,name='logout'),
    path('sign_up_user', views.signUpUser,name='sign_up_user'),
    ]
)

# For d3 charts
urlpatterns.extend(
    [
    path('heatmap-data/', views.heatmap_data, name='heatmap_data'),
    ]
)

# Stats pages
urlpatterns.extend(
    [
    path('stats/players/', views.player_stats_overview, name='player_stats'),
    path('stats/players/<int:player_id>/', views.player_detail_stats, name='player_detail'),
    path('stats/courses/', views.course_stats_overview, name='course_stats'),
    path('stats/courses/<int:course_id>/', views.course_detail_stats, name='course_detail'),
    ]
)

# Admin management URLs
urlpatterns.extend(
    [
    path('admin/bulk-highlight-link/', admin_views.bulk_highlight_link, name='admin_bulk_highlight_link'),
    path('admin/highlight-management/', admin_views.highlight_management, name='admin_highlight_management'),
    path('admin/ajax/toggle-highlight/', admin_views.ajax_toggle_highlight, name='admin_ajax_toggle_highlight'),
    path('rounds/<int:round_id>/add-highlight/', admin_views.add_round_highlight, name='add_round_highlight'),
    ]
)

# Notification URLs
urlpatterns.extend(
    [
    path('notifications/settings/', views_notifications.notifications_settings, name='notifications_settings'),
    path('notifications/toggle/', views_notifications.toggle_notifications, name='toggle_notifications'),
    path('notifications/test/', views_notifications.test_notification, name='test_notification'),
    path('notifications/subscribe/', views_notifications.save_subscription, name='save_subscription'),
    path('notifications/preferences/', views_notifications.update_preferences, name='update_preferences'),
    path('notifications/device/toggle/', views_notifications.toggle_device, name='toggle_device'),
    path('notifications/device/delete/', views_notifications.delete_device, name='delete_device'),
    ]
)

# Development-only URLs
if settings.DEBUG:
    urlpatterns.append(
        path('components/', showcase.component_showcase, name='component_showcase')
    )