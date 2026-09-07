from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.login_view,
        name='login'
    ),

    path(
        'forgot-password/',
        views.forgot_password,
        name='forgot_password'
    ),

]