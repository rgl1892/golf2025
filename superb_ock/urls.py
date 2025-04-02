from django.urls import path

from . import views

urlpatterns = [
    path("",views.Home.as_view() , name="home"),
    path("new_round",views.NewRound.as_view() , name="new_round"),
    path("rounds",views.RoundsOverview.as_view() , name="rounds_overview"),
    path("rounds/<int:round_id>",views.GolfRoundView.as_view() , name="golf_round"),
    path("rounds/<int:round_id>/<int:hole_number>",views.EditScore.as_view() , name="edit_score"),

    path('login',views.logInUser,name='login'),
    path('logout',views.logOutUser,name='logout'),
    path('sign_up_user', views.signUpUser,name='sign_up_user'),
]