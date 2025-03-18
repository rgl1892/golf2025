from django.urls import path

from . import views

urlpatterns = [
    path("",views.Home.as_view() , name="home"),
    path('login',views.logInUser,name='login'),
    path('logout',views.logOutUser,name='logout'),
    path('sign_up_user', views.signUpUser,name='sign_up_user'),
]