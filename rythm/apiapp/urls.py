from django.conf.urls import url, include
from apiapp import views


urlpatterns = [

    # Account related APIs
    url(r'^account/register/$', views.Register.as_view()),
	url(r'^account/login/$', views.LoginView.as_view()),

    ]