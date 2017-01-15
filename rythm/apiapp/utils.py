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