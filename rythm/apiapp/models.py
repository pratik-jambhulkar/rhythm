from django.core.urlresolvers import reverse
from django_mongoengine import Document, fields, EmbeddedDocument, DynamicDocument
import datetime
import uuid
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator


class NotificationDetails(EmbeddedDocument):
	_id = fields.StringField(unique=False, default=None, blank=True, allow_null=True)
	image_url = fields.StringField(unique=False, default=None, blank=True, allow_null=True)
	title = fields.StringField(unique=False, default=None, blank=True, allow_null=True)
	description = fields.StringField(unique=False, default=None, blank=True, allow_null=True)

class Notifications(EmbeddedDocument):
	user_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)
	notification_received_at = fields.DateTimeField(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
		unique=False)
	notification_type = fields.IntField()
	notification_details = fields.EmbeddedDocumentField(NotificationDetails, required=False, 
		default= None, blank=True,unique=False)

class RequestedUsers(EmbeddedDocument):
	user_id = fields.StringField(unique=False)

class PendingRequests(EmbeddedDocument):
	user_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)

class FollowerList(EmbeddedDocument):
	user_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)

class FollowingList(EmbeddedDocument):
	user_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)

class Users(Document):
	created_at = fields.DateTimeField(
		default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
		required=True, editable=False,unique=False
	)
	user_id = fields.StringField(max_length=36,required=True,unique=True)
	username = fields.StringField(unique=True, max_length=30)
	email_id = fields.EmailField(unique=True, max_length=254)
	first_name = fields.StringField(max_length=30, required=False, allow_null=True,unique=False)
	last_name = fields.StringField(max_length=30, required=False, null=True,unique=False)
	profile_url = fields.StringField(
		default = "http://profile.ak.fbcdn.net/static-ak/rsrc.php/v2/yo/r/UlIqmHJn-SK.gif",unique=False
	)
	followed_users_list = fields.EmbeddedDocumentListField(FollowingList, required=False, 
		default= [], blank=True,unique=False)
	follower_users_list = fields.EmbeddedDocumentListField(FollowerList, required=False, 
		default= [], blank=True,unique=False)
	gender = fields.StringField(default=None,unique=False, blank=True, required=False)
	push_notifications = fields.BooleanField(default=True, unique=False)
	token = fields.StringField(default=None, blank=True)
	# phone_number = fields.StringField(min_length=10, max_length=10,blank=True, default=None, required=False)
	notifications = fields.EmbeddedDocumentListField(Notifications, required=False, 
		default= [], blank=True,unique=False)
	is_unread_notification = fields.BooleanField(default=False)
	user_bio = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_genre = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_artist = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_instrument = fields.StringField(default=None,unique=False, blank=True, required=False)
	farorite_album = fields.StringField(default=None,unique=False, blank=True, required=False)
	date_of_birth = fields.StringField(default=None,blank=True, required=False)
	gender = fields.StringField(default=None,blank=True, required=False)
	pending_requests = fields.EmbeddedDocumentListField(PendingRequests, required=False, 
		default= [], blank=True,unique=False)
	requested_users = fields.EmbeddedDocumentListField(RequestedUsers, required=False, 
		default= [], blank=True,unique=False)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)	

class LoginDetails(Document):
	username = fields.StringField(max_length=16, required=True)
	password = fields.StringField(max_length=32, required=True)

class ForgotPassword(Document):
	email_id = fields.EmailField(required=True)

class Logout(Document):
	user_id = fields.StringField(max_length=36, required=True)

class UpdateGCMRequest(Document):
	gcm_token = fields.StringField(required=True)
	user_id = fields.StringField(required=True)

class LoginWithFacebookRequest(Document):
	access_token = fields.StringField(required=True)
	user_id = fields.StringField(required=True)

class LoginWithGoogleRequest(Document):
	access_token = fields.StringField(required=True)

class UpdateBasicInfo(Document):
	user_id = fields.StringField(max_length=36,required=True,unique=False)
	profile_url = fields.StringField(
		default = "http://profile.ak.fbcdn.net/static-ak/rsrc.php/v2/yo/r/UlIqmHJn-SK.gif",unique=False, required=True
	)
	user_bio = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_genre = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_artist = fields.StringField(default=None,unique=False, blank=True, required=False)
	favorite_instrument = fields.StringField(default=None,unique=False, blank=True, required=False)
	farorite_album = fields.StringField(default=None,unique=False, blank=True, required=False)
	date_of_birth = fields.StringField(default=None,blank=True, required=False)
	gender = fields.StringField(default=None,blank=True, required=False)

class LikeDetails(EmbeddedDocument):
	user_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)

class CommentDetails(EmbeddedDocument):
	comment_id = fields.StringField(unique=False)
	notification_id = fields.StringField(unique=False)
	user_id = fields.StringField(unique=False)
	comment = fields.StringField(unique=False)

class RhythmPosts(Document):
	post_id = fields.StringField(max_length=36,required=True,unique=True)
	user_id = fields.StringField(required=True, max_length=36)
	poster_url = fields.StringField(
		default = "http://profile.ak.fbcdn.net/static-ak/rsrc.php/v2/yo/r/UlIqmHJn-SK.gif",
		unique=False, required=True
	)
	created_at = fields.DateTimeField(
		default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		, required=True, unique=False
	)
	post_likes = fields.EmbeddedDocumentListField(LikeDetails, required=False, 
		default= [], blank=True,unique=False)
	total_likes = fields.IntField(default=0)
	post_comments = fields.EmbeddedDocumentListField(CommentDetails, required=False, 
		default= [], blank=True,unique=False)
	total_comments = fields.IntField(default=0)
	is_comment_allowed = fields.BooleanField(default=True)
	post_caption = fields.StringField(unique=False, required=False, null=True)
	song_name = fields.StringField(unique=False, required=True)
	album = fields.StringField(unique=False, required=False, null=True)
	ratings = fields.IntField(min_value=0, max_value=5, default=0)