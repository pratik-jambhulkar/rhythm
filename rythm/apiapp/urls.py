from django.conf.urls import url, include
from apiapp import views


urlpatterns = [

    # Account related APIs
    url(r'^account/register/$', views.Register.as_view()),
	url(r'^account/login/$', views.LoginView.as_view()),
	url(r'^account/logout/$', views.LogoutView.as_view()),
	url(r'^account/forgot-password/$', views.ForgotPasswordView.as_view()),
	url(r'^account/username-availability/(?P<username>[A-Za-z0-9_]+)/$', views.GetUsernameAvailabilityPreLoginView.as_view()),
	url(r'^account/facebook-login/$', views.LoginWithFacebookView.as_view()),
	url(r'^account/google-login/$', views.LoginWithGoogleView.as_view()),
	url(r'^account/update-gcm-token/$', views.UpdateGCMTokenView.as_view()),

	# Profile related APIs
	url(r'^user-profile/get-profile-info/(?P<user_id>[A-Za-z0-9-]+)/$', views.GetUserProfileView.as_view()),
	url(r'^user-profile/update-basic-info/$', views.UpdateUserProfileView.as_view()),

	# Addiing User related APIs
	url(r'^follow-user/send-request/$', views.FollowRequestView.as_view()),
	url(r'^follow-user/accept-request/$', views.AcceptFollowerRequestView.as_view()),
	url(r'^follow-user/remove-follower/$', views.RemoveFollowerView.as_view()),
	url(r'^follow-user/unfollow-user/$', views.UnFollowUserView.as_view()),
	url(r'^follow-user/search-user/(?P<user_id>[A-Za-z0-9-]+)/(?P<search_query>[A-Za-z0-9_]+)/$', views.SearchUserView.as_view()),
	url(r'^follow-user/get-followers/(?P<user_id>[A-Za-z0-9-]+)/$', views.GetFollowersView.as_view()),
	url(r'^follow-user/get-followed/(?P<user_id>[A-Za-z0-9-]+)/$', views.GetFollowedUsersView.as_view()),
	url(r'^follow-user/get-other-followers/(?P<user_id>[A-Za-z0-9-]+)/(?P<other_user_id>[A-Za-z0-9-]+)/$', views.GetOtherUsersFollowersView.as_view()),
	url(r'^follow-user/get-other-followed-users/(?P<user_id>[A-Za-z0-9-]+)/(?P<other_user_id>[A-Za-z0-9-]+)/$', 
		views.GetOtherUsersFollowedUsersView.as_view()),

	# Notification Related APIs
    url(r'^notifications/get-notifications/(?P<user_id>[A-Za-z0-9-]+)/$', views.GetNotificationsView.as_view()),
    url(r'^notifications/update-read-notifications/(?P<user_id>[A-Za-z0-9-]+)/$', 
        views.UpdateNotificationReadView.as_view()),

    # Post Related APIs
    url(r'^posts/create-post/$', views.CreateANewPostView.as_view()),
    url(r'^posts/like-post/$', views.LikePostView.as_view()),
    url(r'^posts/comment-post/$', views.CommentPostView.as_view()),
    url(r'^posts/delete-post/$', views.DeletePostView.as_view()),

    ]