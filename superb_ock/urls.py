from django.urls import path

from . import views, admin_views
from .views_stats import stats, player_stats, course_stats

urlpatterns = [
    path("",views.Home.as_view() , name="home"),
    path("new_round",views.NewRound.as_view() , name="new_round"),
    path("rounds",views.RoundsOverview.as_view() , name="rounds_overview"),
    path("rounds/<int:round_id>",views.GolfRoundView.as_view() , name="golf_round"),
    path("rounds/<int:round_id>/<int:hole_number>",views.EditScore.as_view() , name="edit_score"),
    path("event/<int:event_id>",views.EventView.as_view(), name='event'),
    path("heatmap/",views.HeatMap.as_view() , name="heatmap"),
    path("highlights/",views.HighlightsView.as_view() , name="highlights"),

    
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
    path('heatmap-data/', stats.heatmap_data, name='heatmap_data'),
    ]
)

# Stats pages
urlpatterns.extend(
    [
    path('stats/players/', player_stats.player_stats_overview, name='player_stats'),
    path('stats/players/<int:player_id>/', player_stats.player_detail_stats, name='player_detail'),
    path('stats/courses/', course_stats.course_stats_overview, name='course_stats'),
    path('stats/courses/<int:course_id>/', course_stats.course_detail_stats, name='course_detail'),
    ]
)

# Admin management URLs
urlpatterns.extend(
    [
    path('admin/bulk-highlight-link/', admin_views.bulk_highlight_link, name='admin:bulk_highlight_link'),
    path('admin/highlight-management/', admin_views.highlight_management, name='admin:highlight_management'),
    path('admin/ajax/toggle-highlight/', admin_views.ajax_toggle_highlight, name='admin:ajax_toggle_highlight'),
    path('rounds/<int:round_id>/add-highlight/', admin_views.add_round_highlight, name='add_round_highlight'),
    ]
)