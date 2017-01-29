from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from apiapp.models import Users

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

def get_basic_user_info(user_object):

	user_details = {}

	user_details['user_id'] = user_object['user_id']
	user_details['username'] = user_object['username']
	user_details['profile_url'] = user_object['profile_url']
	user_details['first_name'] = user_object['first_name']
	user_details['last_name'] = user_object['last_name']

	return user_details

def get_user_details(user_object):
	profile_data = {}
	profile_data['user_id'] = user_object.user_id
	profile_data['username'] = user_object.username
	profile_data['profile_url'] = user_object.profile_url
	profile_data['first_name'] = user_object.first_name
	profile_data['last_name'] = user_object.last_name
	profile_data['email_id'] = user_object.email_id
	profile_data['user_bio'] = user_object.user_bio
	profile_data['favorite_genre'] = user_object.favorite_genre
	profile_data['favorite_artist'] = user_object.favorite_artist
	profile_data['favorite_instrument'] = user_object.favorite_instrument
	profile_data['farorite_album'] = user_object.farorite_album
	profile_data['date_of_birth'] = user_object.date_of_birth
	profile_data['gender'] = user_object.gender
	profile_data['follower_users_list'] = len(user_object.follower_users_list)
	profile_data['followed_users_list'] = len(user_object.followed_users_list)
	return profile_data

def is_requested(source_user_id, target_user_id):
	"""
		Function to check whether the target's user id is present in the requested list of the source
		returns 1 if its there
	"""
	requested_result = Users.objects(user_id=source_user_id,
					requested_users__user_id=target_user_id)
	return len(requested_result)

def is_followed(source_user_id, target_user_id):
	"""
		Function to check whether the target's user id is present in the source's followed list
		returns 1 if its there
	"""
	requested_result = Users.objects(user_id=source_user_id,
					followed_users_list__user_id=target_user_id)
	return len(requested_result)

def is_follower(source_user_id, target_user_id):
	"""
		Function to check whether the target's user id is present in the source's followed list
		returns 1 if its there
	"""
	follower_result = Users.objects(user_id=source_user_id,
					follower_users_list__user_id=target_user_id)
	return len(follower_result)

def is_pending(source_user_id, target_user_id):
	"""
		Function to check whether the target's user id is present in the pending list of the source
		returns 1 if its there
	"""
	pending_result = Users.objects(user_id=source_user_id,
					pending_requests__user_id=target_user_id)
	return len(pending_result)

def remove_from_pending(source_user_id, target_user_id):
	"""
		Function to remove the receiver's user id from pending list of the requester
	"""
	Users.objects(user_id=source_user_id).update_one(pull__pending_requests__user_id = target_user_id)
	Users.objects(user_id=target_user_id).update_one(pull__requested_users__user_id=source_user_id)


def get_post_details(post_object):
    """
    Returns a dictionary with the post details from the post object
    """
    post_data = {}
    post_data['poster_url'] = post_object['poster_url']
    post_data['post_id'] = post_object['post_id']
    post_data['user_id'] = post_object['user_id']
    # post_data['post_likes'] = post_object['post_likes']
    post_data['created_at'] = post_object['created_at']
    # post_data['post_comments'] = post_object['post_comments']
    post_data['total_likes'] = post_object['total_likes']
    post_data['total_comments'] = post_object['total_comments']
    post_data['is_comment_allowed'] = post_object['is_comment_allowed']
    post_data['post_caption'] = post_object['post_caption']
    post_data['song_name'] = post_object['song_name']
    post_data['album'] = post_object['album']
    post_data['ratings'] = post_object['ratings']
    
    return post_data

def is_post_liked(user_id,post_object):
    """
    Returns true if the user has liked a post
    """
    has_liked_post = False
    for like_object in post_object.post_likes:
        if like_object.user_id == user_id:
            has_liked_post = True
            break

    return has_liked_post

def has_user_commented(user_id, comment_id,post_comments):

	is_comment = False
	notification_id = None
	for comment in post_comments:
		if comment.user_id == user_id and comment.comment_id == comment_id:
			is_comment = True
			notification_id = comment.notification_id
			break

	return notification_id, is_comment

def get_notification_id(comment_id,post_comments):
	notification_id = None
	for comment in post_comments:
		if comment.comment_id == comment_id:
			notification_id = comment.notification_id
			break

	return notification_id

def get_report_details(report):
	report_detail = {}

	report_detail['created_at'] = report.created_at
	report_detail['report_type'] = report.report_type
	report_detail['report_id'] = report.report_id

	return report_detail