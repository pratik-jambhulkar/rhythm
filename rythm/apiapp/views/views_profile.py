from django.contrib.auth.models import User, Group
from rest_framework import viewsets, authentication
from apiapp.serializers import *
from apiapp.models import Users
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from mongoengine import Q
from response_codes_messages import *

class GetUserProfileView(generics.ListAPIView):
	"""
    Get the connections list of a particular user
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	lookup_url_kwarg = "user_id"
	def get(self, request, user_id):
		response = {}
		try:

			# Get the user details in the dictionary 
			user_profile = Users.objects(user_id=user_id).first()
			
			profile_data = {}
			profile_data['user_id'] = user_profile.user_id
			profile_data['username'] = user_profile.username
			profile_data['profile_url'] = user_profile.profile_url
			profile_data['first_name'] = user_profile.first_name
			profile_data['last_name'] = user_profile.last_name
			profile_data['phone_number'] = user_profile.phone_number
			profile_data['email_id'] = user_profile.email_id

			response['code'] = PROFILE_GET_DETAILS_SUCCESS_CODE
			response['message'] = PROFILE_GET_DETAILS_SUCCESS_MESSAGE
			response['data'] = profile_data
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			response['code'] = PROFILE_GET_DETAILS_INVALID_USERID_CODE
			response['message'] = PROFILE_GET_DETAILS_INVALID_USERID_MESSAGE
			response['data'] = None
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

class UpdateUserProfileView(APIView):
	"""
    Update a User's Profile
    """

	authentication_classes = (authentication.TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	parser_classes = (JSONParser,)
	serializer_class = UserBasicInfoSerializer

	def put(self, request):
		data = JSONParser().parse(request)
		user_data_serializer = UserBasicInfoSerializer(data=data)
		response = {}

		if user_data_serializer.is_valid():

			try:

				user=Users.objects(user_id=data['user_id']).update(user_bio=data['user_bio'],
						profile_url=data['profile_url'], favorite_genre=data['favorite_genre'],
						favorite_artist=data['favorite_artist'], favorite_instrument=data['favorite_instrument'],
						farorite_album=data['farorite_album'], date_of_birth=data['date_of_birth'])
				
				# Get the updated data to send it back 
				users = Users.objects.get(user_id=data['user_id'])
				profile_data = {}
				profile_data['user_id'] = users.user_id
				profile_data['username'] = users.username
				profile_data['profile_url'] = users.profile_url
				profile_data['first_name'] = users.first_name
				profile_data['last_name'] = users.last_name
				profile_data['phone_number'] = users.phone_number
				profile_data['email_id'] = users.email_id

				response['code'] = PROFILE_UPDATE_SUCCESS_CODE
				response['message'] = PROFILE_UPDATE_SUCCESS_MESSAGE
				response['data'] = profile_data
				return Response(response, status= status.HTTP_200_OK)
			except Exception as e:
				response['code'] = PROFILE_UPDATE_INVALID_USERID_CODE
				response['message'] = PROFILE_UPDATE_INVALID_USERID_MESSAGE
				response['data'] = e.args
				return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = PROFILE_UPDATE_MISSING_FIELDS_CODE
			response['message'] = PROFILE_UPDATE_MISSING_FIELDS_MESSAGE
			for key, value in user_data_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)

# class UpdateUserProfileView(APIView):
# 	"""
#     Update a User's Profile
#     """

# 	authentication_classes = (authentication.TokenAuthentication,)
# 	permission_classes = (IsAuthenticated,)
# 	parser_classes = (JSONParser,)
# 	serializer_class = UpdateProfileSerializer

# 	def patch(self, request):
# 		data = JSONParser().parse(request)
# 		user_data_serializer = UpdateProfileSerializer(data=data)
# 		response = {}

# 		if user_data_serializer.is_valid():

# 			try:

# 				# Get the users objects from the database to update
# 				users = Users.objects.get(user_id=data['user_id'])

# 				# Update the username and email in the django database
# 				user_object = User.objects.get(username = users['username'])
# 				user_object.username = data['username']
# 				user_object.email = data['email_id']
# 				user_object.save()

# 				# Check whether the user has entered the phone number and then update the database
# 				if user_data_serializer['phone_number'].value is not None:
# 					user=Users.objects(user_id=data['user_id']).update(username=data['username'],
# 						profile_url=data['profile_url'], first_name=data['first_name'],
# 						last_name=data['last_name'], email_id=data['email_id'],
# 						phone_number=data['phone_number'])
# 				else:
# 					user=Users.objects(user_id=data['user_id']).update(username=data['username'],
# 						profile_url=data['profile_url'], first_name=data['first_name'],
# 						last_name=data['last_name'], email_id=data['email_id'])

# 				# Get the updated data to send it back 
# 				users = Users.objects.get(user_id=data['user_id'])
# 				profile_data = {}
# 				profile_data['user_id'] = users.user_id
# 				profile_data['username'] = users.username
# 				profile_data['profile_url'] = users.profile_url
# 				profile_data['first_name'] = users.first_name
# 				profile_data['last_name'] = users.last_name
# 				profile_data['phone_number'] = users.phone_number
# 				profile_data['email_id'] = users.email_id

# 				response['code'] = PROFILE_UPDATE_SUCCESS_CODE
# 				response['message'] = PROFILE_UPDATE_SUCCESS_MESSAGE
# 				response['data'] = profile_data
# 				return Response(response, status= status.HTTP_200_OK)
# 			except Exception as e:
# 				response['code'] = PROFILE_UPDATE_INVALID_USERID_CODE
# 				response['message'] = PROFILE_UPDATE_INVALID_USERID_MESSAGE
# 				response['data'] = e.args
# 				return Response(response, status= status.HTTP_400_BAD_REQUEST)
# 		else:
# 			error_dict = {}
# 			response['code'] = PROFILE_UPDATE_MISSING_FIELDS_CODE
# 			response['message'] = PROFILE_UPDATE_MISSING_FIELDS_MESSAGE
# 			for key, value in user_data_serializer.errors.items():
# 				error_dict[key] = value[0]
# 			response['data'] = error_dict
# 			return Response(response, status= status.HTTP_400_BAD_REQUEST)


# class GetUsernameAvailabilityPostLoginView(APIView):
#     """
#     Get the username availability Post Login
#     """

#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     parser_classes = (JSONParser,)
#     lookup_url_kwarg = "username"
#     def get(self, request, user_id, username):
#         response = {}

#         try:
#         	# Checks whether the give user id is valid or not
#             user_id_validation = Users.objects.get(user_id=user_id)

#             # Check whether entered username is present in the database such that it should not match
#             # the requester's username
#             user_object = Users.objects( Q(username=username) & Q(user_id__ne=user_id)).first()

#             # Return the response according the username availability
#             if user_object is None:
#                 response['code'] = PROFILE_USERNAME_AVAILABLE_CODE
#                 response['message'] = PROFILE_USERNAME_AVAILABLE_MESSAGE
#                 response['data'] = None
#                 return Response(response, status= status.HTTP_200_OK)
#             else:
#                 response['code'] = PROFILE_USERNAME_NOT_AVAILABLE_CODE
#                 response['message'] = PROFILE_USERNAME_NOT_AVAILABLE_MESSAGE
#                 response['data'] = None
#                 return Response(response, status= status.HTTP_400_BAD_REQUEST)
#         except DoesNotExist as e:

#             response['code'] = PROFILE_USERNAME_DATA_EXCEPTION_CODE
#             response['message'] = PROFILE_USERNAME_DATA_EXCEPTION_MESSAGE
#             response['data'] = None
#             return Response(response, status= status.HTTP_400_BAD_REQUEST)

# class GetOtherUserProfileView(generics.ListAPIView):
# 	"""
#     Get the connections list of a particular user
#     """

# 	authentication_classes = (authentication.TokenAuthentication,)
# 	permission_classes = (IsAuthenticated,)
# 	parser_classes = (JSONParser,)
# 	lookup_url_kwarg = "user_id"
# 	def get(self, request, user_id, other_user_id):
# 		response = {}

# 		try:

# 			# Get the user details in the dictionary 
# 			user_profile = Users.objects(user_id=user_id).first()

# 			other_user_profile = Users.objects(user_id=other_user_id).first()
			
# 			profile_data = {}
# 			profile_data['user_id'] = other_user_profile.user_id
# 			profile_data['username'] = other_user_profile.username
# 			profile_data['profile_url'] = other_user_profile.profile_url
# 			profile_data['first_name'] = other_user_profile.first_name
# 			profile_data['last_name'] = other_user_profile.last_name
# 			profile_data['phone_number'] = other_user_profile.phone_number

# 			# A flag to maintain whether any condition is satisfied before the default condition
# 			flag = False
# 			# Check whether the post owner user is same to the requester
# 			if other_user_id == user_id:
# 			    # if match is found then add it to the list and set the flag
# 			    profile_data['profile_type'] = 100     #The user profile is same
# 			    flag = True

# 			if not flag:
# 			    # Check whether the post owner user is in the blocked list of the requester
# 			    for blocked_user in user_profile.blocked_users:
# 			        # if match is found then skip the record and set the flag
# 			        if other_user_id == blocked_user.user_id:
# 			            profile_data['profile_type'] = 101     #The other user is blocked by me
# 			            flag = True
# 			            break

# 			if not flag:
# 			    # Check whether the post owner user is in the blocked list of other user
# 			    for blocked_by_user in user_profile.blocked_by_users:
# 			        # if match is found then skip the record and set the flag
# 			        if other_user_id == blocked_by_user.user_id:
# 			            profile_data['profile_type'] = 102     #The other user has blocked me
# 			            flag = True
# 			            break

# 			if not flag:
# 			    # Check whether the post owner user is connected to the requester
# 			    for connection in user_profile.connections:
# 			        # if match is found then add it to the list and set the flag
# 			        if other_user_id == connection.user_id:
# 			            profile_data['profile_type'] = 103     #The other user is connected with me
# 			            flag = True
# 			            break

# 			if not flag:
# 			    # Check whether the post owner user is in the requested list of the requester
# 			    for requested_user in user_profile.requested_users:
# 			        # if match is found then add it to the list and set the flag
# 			        if other_user_id == requested_user.user_id:
# 			            profile_data['profile_type'] = 104     #The other user has been requested for connection
# 			            flag = True
# 			            break

# 			if not flag:
# 			    # Check whether the post owner user is in the pending list of the requester
# 			    for pending_request in user_profile.pending_requests:
# 			        # if match is found then add it to the list and set the flag
# 			        if other_user_id == pending_request.user_id:
# 			            profile_data['profile_type'] = 105     #The other user's connection request is pending with requester
# 			            flag = True
# 			            break

# 			# Check if all above conditions are not satisfied then add it to the list with not 
# 			# connected as type
# 			if not flag:
# 			    profile_data['profile_type'] = 106
			

# 			response['code'] = PROFILE_GET_OTHER_USER_DETAILS_SUCCESS_CODE
# 			response['message'] = PROFILE_GET_OTHER_USER_DETAILS_SUCCESS_MESSAGE
# 			response['data'] = profile_data
# 			return Response(response, status= status.HTTP_200_OK)
# 		except Exception as e:
# 			response['code'] = PROFILE_GET_OTHER_USER_DETAILS_INVALID_USERID_CODE
# 			response['message'] = PROFILE_GET_OTHER_USER_DETAILS_INVALID_USERID_MESSAGE
# 			response['data'] = None
# 			return Response(response, status= status.HTTP_400_BAD_REQUEST)