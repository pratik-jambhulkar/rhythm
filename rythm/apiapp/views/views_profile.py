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
from utils import get_user_details

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
			user_object = Users.objects(user_id=user_id).first()
			
			profile_data = get_user_details(user_object)

			posts = RhythmPosts.objects(user_id=user_id)

			profile_data['no_of_posts'] = len(posts)

			response['code'] = PROFILE_GET_DETAILS_SUCCESS_CODE
			response['message'] = PROFILE_GET_DETAILS_SUCCESS_MESSAGE
			response['data'] = profile_data
			return Response(response, status= status.HTTP_200_OK)
		except Exception as e:
			print (e)
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

				user=Users.objects.get(user_id=data['user_id'])

				# Update the username and email in the django database
				user_object = User.objects.get(username = user['username'])
				user_object.username = data['username']
				user_object.email = data['email_id']
				user_object.set_password(data['password'])
				user_object.save()

				user=Users.objects(user_id=data['user_id']).update(user_bio=data['user_bio'],
						profile_url=data['profile_url'], favorite_genre=data['favorite_genre'],
						favorite_artist=data['favorite_artist'], date_of_birth=data['date_of_birth'],
						gender=data['gender'], username=data['username'], email_id=data['email_id'])
				
				# Get the updated data to send it back 
				users = Users.objects.get(user_id=data['user_id'])

				profile_data = get_user_details(users)

				posts = RhythmPosts.objects(user_id=data['user_id'])

				profile_data['no_of_posts'] = len(posts)

				response['code'] = PROFILE_UPDATE_SUCCESS_CODE
				response['message'] = PROFILE_UPDATE_SUCCESS_MESSAGE
				response['data'] = profile_data
				return Response(response, status= status.HTTP_200_OK)
			except Exception as e:
				print (e)
				response['code'] = PROFILE_UPDATE_INVALID_USERID_CODE
				response['message'] = PROFILE_UPDATE_INVALID_USERID_MESSAGE
				response['data'] = None
				return Response(response, status= status.HTTP_400_BAD_REQUEST)
		else:
			error_dict = {}
			response['code'] = PROFILE_UPDATE_MISSING_FIELDS_CODE
			response['message'] = PROFILE_UPDATE_MISSING_FIELDS_MESSAGE
			for key, value in user_data_serializer.errors.items():
				error_dict[key] = value[0]
			response['data'] = error_dict
			return Response(response, status= status.HTTP_400_BAD_REQUEST)