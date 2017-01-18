from django.contrib.auth.models import User
from rest_framework import viewsets, authentication
from apiapp.serializers import FollowRequestSerializer
from apiapp.models import *
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework import status, generics
from mongoengine import Q
import uuid
import datetime
import sys
import os
sys.path.insert(1, sys.path[0]+'/apiapp')

from response_codes_messages import *
from utils import *

class FollowRequestView(APIView):
	"""
    Sends a follower request from one user to another 
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	serializer_class = FollowRequestSerializer

	def post(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				source_user_id = data['source_user_id']
				target_user_id = data['target_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=source_user_id).only('user_id') and Users.objects(user_id=target_user_id).only('user_id'):

					# Checks whether connection request is already sent to the other user
					if is_requested(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						response['code'] = FOLLOW_REQUEST_SENT_ERROR_CODE
						response['message'] = FOLLOW_REQUEST_SENT_ERROR_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)

					# Checks whether the users are already followed
					if is_followed(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						response['code'] = FOLLOW_REQUEST_DATA_EXCEPTION_CODE
						response['message'] = FOLLOW_REQUEST_DATA_EXCEPTION_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)

					# Create a notification id for inserting in the notifications of other user
					notification_id = str(uuid.uuid4())
					current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

					notification_object = Notifications(user_id = source_user_id,
						notification_id = notification_id,
					    notification_received_at = current_time, notification_type = 0, 
					    notification_details = None)

					# Pushes the user id of requested user into the database
					Users.objects(user_id=source_user_id).update_one(push__requested_users={'user_id' : target_user_id})

					# Pushes the user id of the requester and the notification of the pending request into the database
					Users.objects(user_id=target_user_id).update_one(push__pending_requests={'user_id' : source_user_id,
						'notification_id' : notification_id }, push__notifications=notification_object,
						set__is_unread_notification=True)

					response['code'] = FOLLOW_REQUEST_SUCCESS_CODE
					response['message'] = FOLLOW_REQUEST_SUCCESS_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_200_OK)
				else:
					response['code'] = FOLLOW_REQUEST_INVALID_USERID_CODE
					response['message'] = FOLLOW_REQUEST_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = FOLLOW_REQUEST_INVALID_USERID_CODE
				response['message'] = FOLLOW_REQUEST_INVALID_USERID_MESSAGE
				response['data'] = None
				return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = FOLLOW_REQUEST_MISSING_FIELDS_CODE
			response['message'] = FOLLOW_REQUEST_MISSING_FIELDS_MESSAGE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status=400)

	def delete(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				target_user_id = data['target_user_id']
				source_user_id = data['source_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=target_user_id).only('user_id') and Users.objects(user_id=source_user_id).only('user_id'):

					# Checks whether follower request is pending with other user
					if is_pending(source_user_id=target_user_id, target_user_id=source_user_id) is not 0:
						
						try:

							# Get the user object of the other user from the database
							user = Users.objects(user_id=target_user_id).only('pending_requests').first()

							# Get the notification id of the particular request from the other user's database
							for pending_request in user.pending_requests:
								if pending_request.user_id == source_user_id:
									notification_id = pending_request.notification_id

							# Remove the requests from both users databases and also removes the notification
							# object from other user's database
							Users.objects(user_id=source_user_id).update_one(pull__requested_users__user_id=target_user_id)
							Users.objects(user_id=target_user_id).update_one(pull__pending_requests__user_id=source_user_id,
								pull__notifications__notification_id=notification_id)

							response['code'] = FOLLOW_DELETE_REQUEST_SUCCESS_CODE
							response['message'] = FOLLOW_DELETE_REQUEST_SUCCESS_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_200_OK)
						except Exception as e:
							response['code'] = FOLLOW_DELETE_REQUEST_DATA_EXCEPTION_CODE
							response['message'] = FOLLOW_DELETE_REQUEST_DATA_EXCEPTION_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_400_BAD_REQUEST)
					else:
						response['code'] = FOLLOW_DELETE_REQUEST_NOT_PRESENT_CODE
						response['message'] = FOLLOW_DELETE_REQUEST_NOT_PRESENT_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)
				else:
					response['code'] = FOLLOW_DELETE_REQUEST_INVALID_USERID_CODE
					response['message'] = FOLLOW_DELETE_REQUEST_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = FOLLOW_DELETE_REQUEST_INVALID_USERID_CODE
				response['message'] = FOLLOW_DELETE_REQUEST_INVALID_USERID_MESSAGE
				response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = FOLLOW_DELETE_REQUEST_MISSING_FIELDS_CODE
			response['message'] = FOLLOW_DELETE_REQUEST_MISSING_FIELDS_MESSAGE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

class AcceptFollowerRequestView(APIView):
	"""
    Responds to a follower request either by accepting/deleting
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	serializer_class = FollowRequestSerializer

	def put(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				target_user_id = data['target_user_id']
				source_user_id = data['source_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=target_user_id).only('user_id') and Users.objects(user_id=source_user_id).only('user_id'):

					# Checks whether connection request is pending with the requester
					if is_pending(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						
						# Checks whether the user is already followed
						if is_follower(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
							response['code'] = FOLLOW_ACCEPT_REQUEST_FOLLOW_ERROR_CODE
							response['message'] = FOLLOW_ACCEPT_REQUEST_FOLLOW_ERROR_MESSAGE
							response['data'] = None
							remove_from_pending(source_user_id=source_user_id, target_user_id=target_user_id)
							return Response(response, status= status.HTTP_400_BAD_REQUEST)

						try:

							current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

							# Get the notification id for the particular pending request
							user = Users.objects(user_id=source_user_id).only('pending_requests').first()

							for pending_request in user.pending_requests:
								if pending_request.user_id == target_user_id:
									notification_id = pending_request.notification_id

							# If we successfully find the notification id for the pending request
							if notification_id is not None:

								notification_object_receiver = Notifications(user_id = source_user_id, 
								    notification_id = notification_id,
								    notification_received_at = current_time, notification_type = 2, 
								    notification_details = None)

								notification_object_requester = Notifications(user_id = target_user_id, 
			                        notification_id = notification_id,
			                        notification_received_at = current_time, notification_type = 1, 
			                        notification_details = None)

								# Update the previous type of notification from pending to following from the
								# requester
								Users.objects( Q(user_id=source_user_id) & 
										Q(notifications__notification_id=notification_id) ).update_one(
										notifications__S=notification_object_requester)

								# Push the notification object created for this user
								Users.objects( user_id=target_user_id).update_one(push__notifications=
									notification_object_receiver)

							# Pull the requests from the requested field and pending field from both users
							# database
							Users.objects(user_id=source_user_id).update_one(pull__pending_requests__user_id= target_user_id)
							Users.objects(user_id=target_user_id).update_one(pull__requested_users__user_id= source_user_id)
							
							# Push the new follower and followed by objects in the respective field for both the users
							# with the notification id field and mark unread notification for both users as true
							Users.objects(user_id=source_user_id).update_one(push__follower_users_list={'user_id' : target_user_id
								, 'notification_id' : notification_id }, set__is_unread_notification=True)
							Users.objects(user_id=target_user_id).update_one(push__followed_users_list={'user_id' : source_user_id
								, 'notification_id' : notification_id }, set__is_unread_notification=True)

							response['code'] = FOLLOW_ACCEPT_REQUEST_SUCCESS_CODE
							response['message'] = FOLLOW_ACCEPT_REQUEST_SUCCESS_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_200_OK)
						except Exception as e:
							response['code'] = FOLLOW_ACCEPT_REQUEST_DATA_EXCEPTION_CODE
							response['message'] = FOLLOW_ACCEPT_REQUEST_DATA_EXCEPTION_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_400_BAD_REQUEST)
					else:
						response['code'] = FOLLOW_ACCEPT_REQUEST_NOT_PRESENT_CODE
						response['message'] = FOLLOW_ACCEPT_REQUEST_NOT_PRESENT_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)
				else:
					response['code'] = FOLLOW_ACCEPT_REQUEST_INVALID_USERID_CODE
					response['message'] = FOLLOW_ACCEPT_REQUEST_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = FOLLOW_ACCEPT_REQUEST_INVALID_USERID_CODE
				response['message'] = FOLLOW_ACCEPT_REQUEST_INVALID_USERID_MESSAGE
				response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = FOLLOW_ACCEPT_REQUEST_MISSING_FIELDS_CODE
			response['message'] = FOLLOW_ACCEPT_REQUEST_MISSING_FIELDS_MESSAGE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

	def delete(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				target_user_id = data['target_user_id']
				source_user_id = data['source_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=target_user_id).only('user_id') and Users.objects(user_id=source_user_id).only('user_id'):

					# Checks whether follower request is pending with the requester
					if is_pending(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						
						# Checks whether the users are already connected
						if is_follower(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
							response['code'] = FOLLOW_REJECT_REQUEST_FOLLOW_ERROR_CODE
							response['message'] = FOLLOW_REJECT_REQUEST_FOLLOW_ERROR_MESSAGE
							response['data'] = None
							remove_from_pending(source_user_id=source_user_id)
							return Response(response, status= status.HTTP_400_BAD_REQUEST)

						try:
							# Get the user object the user who is deleting the request
							user = Users.objects(user_id=source_user_id).only('pending_requests').first()

							# Get the notification id for the user who is deleting the request
							for pending_request in user.pending_requests:
								if pending_request.user_id == target_user_id:
									notification_id = pending_request.notification_id

							# Pull the requests from both the users database and also pull the notification
							# object from the requesters database
							Users.objects(user_id=source_user_id).update_one(pull__pending_requests__user_id = target_user_id,
								pull__notifications__notification_id = notification_id)
							Users.objects(user_id=target_user_id).update_one(pull__requested_users__user_id = source_user_id)

							response['code'] = FOLLOW_REJECT_REQUEST_SUCCESS_CODE
							response['message'] = FOLLOW_REJECT_REQUEST_SUCCESS_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_200_OK)
						except Exception as e:
							response['code'] = FOLLOW_REJECT_REQUEST_DATA_EXCEPTION_CODE
							response['message'] = FOLLOW_REJECT_REQUEST_DATA_EXCEPTION_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_400_BAD_REQUEST)
					else:
						response['code'] = FOLLOW_REJECT_REQUEST_NOT_PRESENT_CODE
						response['message'] = FOLLOW_REJECT_REQUEST_NOT_PRESENT_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)
				else:
					response['code'] = FOLLOW_REJECT_REQUEST_INVALID_USERID_CODE
					response['message'] = FOLLOW_REJECT_REQUEST_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = FOLLOW_REJECT_REQUEST_INVALID_USERID_CODE
				response['message'] = FOLLOW_REJECT_REQUEST_INVALID_USERID_MESSAGE
				response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = FOLLOW_REJECT_REQUEST_MISSING_FIELDS_CODE
			response['message'] = FOLLOW_REJECT_REQUEST_MISSING_FIELDS_MESSAGE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)


class RemoveFollowerView(APIView):
	"""
    Removes a follower from the User's database
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	serializer_class = FollowRequestSerializer
	def delete(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				target_user_id = data['target_user_id']
				source_user_id = data['source_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=target_user_id).only('user_id') and Users.objects(user_id=source_user_id).only('user_id'):

					# Checks whether the user is followed by
					if is_follower(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						
						try:

							# Get the notification id of the user who is removing the user to use it
							# further
							user = Users.objects(user_id=source_user_id).only('follower_users_list').first()

							for follower in user.follower_users_list:
								if follower.user_id == target_user_id:
									notification_id = follower.notification_id

							# Pulls the follower and followed by from both users database along with the notifications object
							Users.objects(user_id=source_user_id).update_one(pull__follower_users_list__user_id=target_user_id,
								pull__notifications__notification_id=notification_id)
							Users.objects(user_id=target_user_id).update_one(pull__followed_users_list__user_id=source_user_id,
								pull__notifications__notification_id=notification_id)

							response['code'] = FOLLOWER_DELETE_SUCCESS_CODE
							response['message'] = FOLLOWER_DELETE_SUCCESS_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_200_OK)
						except Exception as e:
							response['code'] = FOLLOWER_DELETE_DATA_EXCEPTION_CODE
							response['message'] = FOLLOWER_DELETE_DATA_EXCEPTION_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_400_BAD_REQUEST)
					else:
						response['code'] = FOLLOWER_DELETE_FOLLOW_ERROR_CODE
						response['message'] = FOLLOWER_DELETE_FOLLOW_ERROR_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)
				else:
					response['code'] = FOLLOWER_DELETE_INVALID_USERID_CODE
					response['message'] = FOLLOWER_DELETE_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = FOLLOWER_DELETE_INVALID_USERID_CODE
				response['message'] = FOLLOWER_DELETE_INVALID_USERID_MESSAGE
				response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = FOLLOWER_DELETE_MISSING_FIELDS_CODE
			response['message'] = FOLLOWER_DELETE_MISSING_FIELDS_CODE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)


class UnFollowUserView(APIView):
	"""
    Removes a followed user from the User's database
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	serializer_class = FollowRequestSerializer
	def delete(self, request):
		data = JSONParser().parse(request)
		request_serializer = FollowRequestSerializer(data=data)
		response = {}

		if request_serializer.is_valid():
			try:
				target_user_id = data['target_user_id']
				source_user_id = data['source_user_id']

				# Checks whether the given user ids are valid or not
				if Users.objects(user_id=target_user_id).only('user_id') and Users.objects(user_id=source_user_id).only('user_id'):

					# Checks whether the user is following other user
					if is_followed(source_user_id=source_user_id, target_user_id=target_user_id) is not 0:
						
						try:

							# Get the notification id of the user who is unfollowing to use it further
							user = Users.objects(user_id=source_user_id).only('followed_users_list').first()

							for followed_user in user.followed_users_list:
								if followed_user.user_id == target_user_id:
									notification_id = followed_user.notification_id

							# Pulls the follower and followed data from both users database along with the notifications object
							Users.objects(user_id=source_user_id).update_one(pull__followed_users_list__user_id=target_user_id,
								pull__notifications__notification_id=notification_id)
							Users.objects(user_id=target_user_id).update_one(pull__follower_users_list__user_id=source_user_id,
								pull__notifications__notification_id=notification_id)

							response['code'] = UNFOLLOW_SUCCESS_CODE
							response['message'] = UNFOLLOW_SUCCESS_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_200_OK)
						except Exception as e:
							response['code'] = UNFOLLOW_DATA_EXCEPTION_CODE
							response['message'] = UNFOLLOW_DATA_EXCEPTION_MESSAGE
							response['data'] = None
							return Response(response, status= status.HTTP_400_BAD_REQUEST)
					else:
						response['code'] = UNFOLLOW_FOLLOW_ERROR_CODE
						response['message'] = UNFOLLOW_FOLLOW_ERROR_MESSAGE
						response['data'] = None
						return Response(response, status= status.HTTP_400_BAD_REQUEST)
				else:
					response['code'] = UNFOLLOW_INVALID_USERID_CODE
					response['message'] = UNFOLLOW_INVALID_USERID_MESSAGE
					response['data'] = None
					return Response(response, status= status.HTTP_400_BAD_REQUEST)
			except Users.DoesNotExist as e:
				response['code'] = UNFOLLOW_INVALID_USERID_CODE
				response['message'] = UNFOLLOW_INVALID_USERID_MESSAGE
				response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = UNFOLLOW_MISSING_FIELDS_CODE
			response['message'] = UNFOLLOW_MISSING_FIELDS_MESSAGE
			for key, value in request_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)


class SearchUserView(generics.ListAPIView):
	"""
    Get the users matching the search queary
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "search_query"

	def get(self, request, user_id, search_query):
		response = {}
		
		try:
			users_list = []

			# Get the data of the requester
			requesters_data = Users.objects(user_id=user_id).first()

			# Get all the users matching the search query according to username, first name or last name
			users = Users.objects( Q(username__icontains=search_query) | 
				Q(first_name__icontains=search_query) | 
				Q(last_name__icontains=search_query))
			
			# Iterate over all the users
			for user in users:

				if user.user_id != user_id:
					user_details_dict = {}
					user_details_dict = get_basic_user_info(user)
					# A flag to maintain whether any condition is satisfied before the default condition
					flag = False

					if not flag:
						# Check whether the current user is followed by the requester
						for followed_user in requesters_data.followed_users_list:
							# if match is found then add it to the list and set the flag
							if user.user_id == followed_user.user_id:
								user_details_dict['type'] = 101
								users_list.append(user_details_dict)
								flag = True
								break

					if not flag:
						# Check whether the current user is in the requested list of the requester
						for requested_user in requesters_data.requested_users:
							# if match is found then add it to the list and set the flag
							if user.user_id == requested_user.user_id:
								user_details_dict['type'] = 102
								users_list.append(user_details_dict)
								flag = True
								break

					if not flag:
						# Check whether the current user is in the pending list of the requester
						for pending_request in requesters_data.pending_requests:
							# if match is found then add it to the list and set the flag
							if user.user_id == pending_request.user_id:
								user_details_dict['type'] = 103
								users_list.append(user_details_dict)
								flag = True
								break

					# Check if all above conditions are not satisfied then add it to the list with normal type
					if not flag:
						user_details_dict['type'] = 100
						users_list.append(user_details_dict)

			response['code'] = SEARCH_USER_SUCCESS_CODE
			response['message'] = SEARCH_USER_SUCCESS_MESSAGE
			response['data'] = users_list
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
			response['code'] = SEARCH_USER_DATA_EXCEPTION_CODE
			response['message'] = SEARCH_USER_DATA_EXCEPTION_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

class GetFollowersView(generics.ListAPIView):
	"""
    Get the follower list of a particular user
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "user_id"
	def get(self, request, user_id):

		response = {}

		try:

			# Get the user object whose followers are to be retrieved
			user = Users.objects(user_id=user_id).only('follower_users_list','requested_users','followed_users_list').first()

			followers_list = []

			# Iterate over all the followers of the user
			for follower in user.follower_users_list:
				current_id = follower.user_id
				user_details_dict = {}

				# Get the object for the current follower
				follower_user = Users.objects(user_id=current_id).only('user_id','profile_url','username',
					'first_name','last_name').first()

				user_details_dict = get_basic_user_info(follower_user)

				# A flag to maintain whether any condition is satisfied before the default condition
				flag = False

				# Check whether the current user is followed by the requester
				for followed_user in user.followed_users_list:
					# if match is found then add it to the list and set the flag
					if follower_user.user_id == followed_user.user_id:
						user_details_dict['type'] = 101
						followers_list.append(user_details_dict)
						flag = True
						break

				if not flag:
					# Check whether the current user is in the requested list of the requester
					for requested_user in user.requested_users:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == requested_user.user_id:
							user_details_dict['type'] = 102
							followers_list.append(user_details_dict)
							flag = True
							break

				if not flag:
					# Append the user to the follower list 
					user_details_dict['type'] = 100
					followers_list.append(user_details_dict)

			# Sort the list according to the username in ascending manner
			sorted_list = sorted(followers_list, key=lambda k: k['username'])

			response['code'] = GET_FOLLOWER_LIST_SUCCESS_CODE
			response['message'] = GET_FOLLOWER_LIST_SUCCESS_MESSAGE
			response['data'] = sorted_list
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
			response['code'] = GET_FOLLOWER_LIST_INVALID_USERID_CODE
			response['message'] = GET_FOLLOWER_LIST_INVALID_USERID_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

class GetFollowedUsersView(generics.ListAPIView):
	"""
    Get the followed user list of a particular user
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "user_id"
	def get(self, request, user_id):

		response = {}

		try:

			# Get the user object whose followed users are to be retrieved
			user = Users.objects(user_id=user_id).only('followed_users_list').first()

			followed_users_list = []

			# Iterate over all the followed users of the user
			for followed_user in user.followed_users_list:
				current_id = followed_user.user_id
				user_details_dict = {}

				# Get the object or the current followed user
				user = Users.objects(user_id=current_id).only('user_id','profile_url','username',
					'first_name','last_name').first()
				
				# Append the user to the followed user list 
				user_details_dict = get_basic_user_info(user)
				followed_users_list.append(user_details_dict)

			# Sort the list according to the username in ascending manner
			sorted_list = sorted(followed_users_list, key=lambda k: k['username'])
			
			response['code'] = GET_FOLLOWED_LIST_SUCCESS_CODE
			response['message'] = GET_FOLLOWED_LIST_SUCCESS_MESSAGE
			response['data'] = sorted_list
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
			response['code'] = GET_FOLLOWED_LIST_INVALID_USERID_CODE
			response['message'] = GET_FOLLOWED_LIST_INVALID_USERID_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)


class GetOtherUsersFollowersView(generics.ListAPIView):
	"""
    Get the follower list of a particular user
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "user_id"
	def get(self, request, user_id, other_user_id):

		response = {}

		try:

			# Get the user object whose followers are to be retrieved
			other_user = Users.objects(user_id=other_user_id).only('follower_users_list').first()

			# Get the requester' object from the database
			user_object = Users.objects(user_id=user_id).only('followed_users','requested_users',
				'pending_requests','profile_url','username','first_name','last_name','user_id').first()

			followers_list = []

			# Iterate over all the followers of the user
			for follower in other_user.follower_users_list:
				current_id = follower.user_id

				follower_user = Users.objects(user_id=current_id).only('user_id','profile_url','username',
					'first_name','last_name').first()
				user_details_dict = {}
				user_details_dict = get_basic_user_info(follower_user)

				# A flag to maintain whether any condition is satisfied before the default condition
				flag = False
				# Check whether the current user is same to the requester
				if follower_user.user_id == user_id:
					# if match is found then add it to the list and set the flag
					user_details_dict['type'] = 104
					followers_list.append(user_details_dict)
					flag = True

				if not flag:
					# Check whether the current user is connected to the requester
					for connection in user_object.followed_users_list:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == connection.user_id:
							user_details_dict['type'] = 101
							followers_list.append(user_details_dict)
							flag = True
							break

				if not flag:
					# Check whether the current user is in the requested list of the requester
					for requested_user in user_object.requested_users:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == requested_user.user_id:
							user_details_dict['type'] = 102
							followers_list.append(user_details_dict)
							flag = True
							break

				if not flag:
					# Check whether the current user is in the pending list of the requester
					for pending_request in user_object.pending_requests:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == pending_request.user_id:
							user_details_dict['type'] = 103
							followers_list.append(user_details_dict)
							flag = True
							break

				# Check if all above conditions are not satisfied then add it to the list with not 
				# connected as type
				if not flag:
					user_details_dict['type'] = 100
					followers_list.append(user_details_dict)

			# Sort the list according to the username in ascending manner
			sorted_list = sorted(followers_list, key=lambda k: k['username'])

			response['code'] = GET_OTHER_FOLLOWER_LIST_SUCCESS_CODE
			response['message'] = GET_OTHER_FOLLOWER_LIST_SUCCESS_MESSAGE
			response['data'] = sorted_list
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
			response['code'] = GET_OTHER_FOLLOWER_LIST_INVALID_USERID_CODE
			response['message'] = GET_OTHER_FOLLOWER_LIST_INVALID_USERID_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

class GetOtherUsersFollowedUsersView(generics.ListAPIView):
	"""
    Get the followed user list of a particular user
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "user_id"
	def get(self, request, user_id, other_user_id):

		response = {}

		try:

			# Get the user object whose followers are to be retrieved
			other_user = Users.objects(user_id=other_user_id).only('followed_users_list').first()

			# Get the requester' object from the database
			user_object = Users.objects(user_id=user_id).only('followed_users','requested_users',
				'pending_requests','profile_url','username','first_name','last_name','user_id').first()

			followed_users_list = []

			# Iterate over all the followers of the user
			for follower in other_user.follower_users_list:
				current_id = follower.user_id

				follower_user = Users.objects(user_id=current_id).only('user_id','profile_url','username',
					'first_name','last_name').first()
				user_details_dict = {}
				user_details_dict = get_basic_user_info(follower_user)

				# A flag to maintain whether any condition is satisfied before the default condition
				flag = False
				# Check whether the current user is same to the requester
				if follower_user.user_id == user_id:
					# if match is found then add it to the list and set the flag
					user_details_dict['type'] = 104
					followers_list.append(user_details_dict)
					flag = True

				if not flag:
					# Check whether the current user is followed by the requester
					for connection in user_object.followed_users_list:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == connection.user_id:
							user_details_dict['type'] = 101
							followed_users_list.append(user_details_dict)
							flag = True
							break

				if not flag:
					# Check whether the current user is in the requested list of the requester
					for requested_user in user_object.requested_users:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == requested_user.user_id:
							user_details_dict['type'] = 102
							followed_users_list.append(user_details_dict)
							flag = True
							break

				if not flag:
					# Check whether the current user is in the pending list of the requester
					for pending_request in user_object.pending_requests:
						# if match is found then add it to the list and set the flag
						if follower_user.user_id == pending_request.user_id:
							user_details_dict['type'] = 103
							followed_users_list.append(user_details_dict)
							flag = True
							break

				# Check if all above conditions are not satisfied then add it to the list as other
				if not flag:
					user_details_dict['type'] = 100
					followed_users_list.append(user_details_dict)

			# Sort the list according to the username in ascending manner
			sorted_list = sorted(followed_users_list, key=lambda k: k['username'])

			response['code'] = GET_OTHER_FOLLOWED_LIST_SUCCESS_CODE
			response['message'] = GET_OTHER_FOLLOWED_LIST_SUCCESS_MESSAGE
			response['data'] = sorted_list
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
			response['code'] = GET_OTHER_FOLLOWED_LIST_INVALID_USERID_CODE
			response['message'] = GET_OTHER_FOLLOWED_LIST_INVALID_USERID_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)