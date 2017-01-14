from django.conf.urls import url, include
from apiapp import views


urlpatterns = [

    # Account related APIs
    url(r'^account/register/$', views.Register.as_view()),
	url(r'^account/login/$', views.LoginView.as_view()),
	url(r'^account/logout/$', views.LogoutView.as_view()),
	url(r'^account/forgot-password/$', views.ForgotPasswordView.as_view()),
	url(r'^account/username-availability/(?P<username>[A-Za-z0-9_]+)/$', views.GetUsernameAvailabilityPreLoginView.as_view()),
	url(r'^account/facebook-login/$', views.LoginView.as_view()),
	url(r'^account/google-login/$', views.LoginView.as_view()),
	url(r'^account/update-gcm-token/$', views.UpdateGCMTokenView.as_view()),

	# Profile related APIs
	url(r'^user-profile/get-profile-info/(?P<user_id>[A-Za-z0-9-]+)/$', views.GetUserProfileView.as_view()),
	url(r'^user-profile/update-basic-info/$', views.UpdateUserProfileView.as_view()),
    ]