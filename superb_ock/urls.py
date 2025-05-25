from django.urls import path

from . import views
from .views_stats import stats

urlpatterns = [
    path("",views.Home.as_view() , name="home"),
    path("new_round",views.NewRound.as_view() , name="new_round"),
    path("rounds",views.RoundsOverview.as_view() , name="rounds_overview"),
    path("rounds/<int:round_id>",views.GolfRoundView.as_view() , name="golf_round"),
    path("rounds/<int:round_id>/<int:hole_number>",views.EditScore.as_view() , name="edit_score"),
    path("event/<int:event_id>",views.EventView.as_view(), name='event'),
    path("heatmap/",views.HeatMap.as_view() , name="heatmap"),

    
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