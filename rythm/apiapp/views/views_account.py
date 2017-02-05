
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, authentication
from apiapp.serializers import *
from apiapp.models import Users
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes, detail_route
from rest_framework.response import Response
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework import status, generics
from push_notifications.models import GCMDevice
import push_notifications
from mongoengine import Q
import requests
import random
from datetime import datetime
import os
import sys

sys.path.insert(1, sys.path[0]+'/apiapp')
from utils import *
from response_codes_messages import *

class LoginView(APIView):
    """
    Logs in the user using Django's authentication
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    serializer_class = LoginSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        data = JSONParser().parse(request)
        login_serializer = LoginSerializer(data=data)
        response = {}
        if login_serializer.is_valid():
            try:
                username = data['username']
                password = data['password']
                user = authenticate(username=username , password=password)
                if user is not None:
                    login(request, user)
                    token, created = Token.objects.get_or_create(user=user)
                    response['code'] = LOGIN_SUCCESS_CODE
                    response['message'] = LOGIN_SUCCESS_MESSAGE + username + ' to rhythm!'

                    # Get the user's data if the user is valid and return the data
                    user_data = Users.objects.get(username=username)

                    # Add the authorization token value to the data
                    user_data.token = token

                    serialized_data = UsersSerializer(user_data)
                    response['data'] = serialized_data.data
                    return JSONResponse(response, status=200)
                else:
                    response['code'] = LOGIN_WRONG_CREDENTIALS_CODE
                    response['message'] = LOGIN_WRONG_CREDENTIALS_MESSAGE
                    response['data'] = None
                    return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                response['code'] = LOGIN_DATA_EXCEPTION_CODE
                response['message'] = LOGIN_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            error_dict = {}
            response['code'] = LOGIN_MISSING_FIELDS_CODE
            response['message'] = LOGIN_MISSING_FIELDS_MESSAGE
            for key, value in login_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

class Register(APIView):
    """
    Register a user in the django auth model and in custom users database
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    serializer_class = RegistrationSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        data = JSONParser().parse(request)
        userid = str(uuid.uuid4())
        data['user_id'] = userid
        serializer = RegistrationSerializer(data=data)
        response = {}

        if serializer.is_valid():
            if 'password' in data:

                # Create a new user in the django's user database
                User.objects.create_user(username=data['username'],email=data['email_id'],
                    password=data['password'])

                # Create a new user in the MongoDb database
                serializer.save()

                response['code'] = REGISTER_SUCCESS_CODE
                response['message'] = REGISTER_SUCCESS_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_201_CREATED)
            else:
                error_dict = {}
                response['code'] = REGISTER_MISSING_PASSWORD_CODE
                response['message'] = REGISTER_MISSING_PASSWORD_MESSAGE
                error_dict['password'] = 'This field is required.'
                response['data'] = error_dict
                return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_dict = {}
            response['code'] = REGISTER_MISSING_FIELD_CODE
            response['message'] = REGISTER_MISSING_FIELD_MESSAGE
            for key, value in serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
            
class LogoutView(APIView):
    """
    Logs out the user from the app
    """
    throttle_classes = ()
    authentication_classes = (authentication.TokenAuthentication, CsrfExemptSessionAuthentication)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = LogoutSerializer

    def post(self, request):
        
        data = JSONParser().parse(request)
        logout_serializer = LogoutSerializer(data=data)
        response = {}

        if logout_serializer.is_valid():
            try:

                # Logout the user
                logout(request)

                user = Users.objects.get(user_id=data['user_id'])

                # Change the state of the GCM device so that he won't receive any push notifications
                user_model = User.objects.get(username=user.username)

                gcmdevice = GCMDevice.objects.get(user=user_model)
                gcmdevice.active = False
                gcmdevice.save()
                
                response['code'] = LOGOUT_SUCCESS_CODE
                response['message'] = LOGOUT_SUCCESS_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_200_OK)
            except Users.DoesNotExist as e:
                response['code'] = LOGOUT_INVALID_USERID_CODE
                response['message'] = LOGOUT_INVALID_USERID_SUCCESS
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
            except GCMDevice.DoesNotExist:
                response['code'] = LOGOUT_GCMDEVICE_ERROR_CODE
                response['message'] = LOGOUT_GCMDEVICE_ERROR_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_dict = {}
            response['code'] = LOGOUT_MISSING_FIELD_CODE
            response['message'] = lOGOUT_MISSING_FIELD_MESSAGE
            for key, value in logout_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    """
    Sends a random generated password to the User's registered email id
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    serializer_class = ForgotPasswordSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        data = JSONParser().parse(request)
        serialized_data = ForgotPasswordSerializer(data=data)

        # Create a random password 
        new_password = User.objects.make_random_password()
        response = {}
        if serialized_data.is_valid():
            email_id = data['email_id']
            try:
                # Check whether the given email id is valid or not
                user = User.objects.get(email=email_id)

            except Exception as e:
                user = None
                response['code'] = FORGOT_PASSWORD_EMAIL_INVALID_CODE
                response['message'] = FORGOT_PASSWORD_EMAIL_INVALID_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password to the User's data
            user.set_password(new_password)
            user.save()

            # Send the new password to the User via email
            send_mail('Rhythm', 'Your new password is: ' + new_password, 'sachinmutthe007@gmail.com', [email_id,], fail_silently=False)
            
            response['code'] = FORGOT_PASSWORD_EMAIL_SUCCESS_CODE
            response['message'] = FORGOT_PASSWORD_EMAIL_SUCCESS_MESSAGE
            response['data'] = None
            return JSONResponse(response, status=status.HTTP_200_OK)
        else:
            error_dict = {}
            response['code'] = FORGOT_PASSWORD_MISSING_FIELD_CODE
            response['message'] = FORGOT_PASSWORD_MISSING_FIELD_MESSAGE
            for key, value in serialized_data.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

class UpdateGCMTokenView(APIView):
    """
    Updates the GCM token of a user after logging in into the app
    """
    throttle_classes = ()
    authentication_classes = (authentication.TokenAuthentication, CsrfExemptSessionAuthentication)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = UpdateGCMRequestSerializer

    def post(self, request):
        data = JSONParser().parse(request)
        udpate_gcm_serializer = UpdateGCMRequestSerializer(data=data)
        response = {}

        if udpate_gcm_serializer.is_valid():
            try:
                # get the user objects from both the database
                complete_user_object = Users.objects.get(user_id=data['user_id'])
                user = User.objects.get(username=complete_user_object['username'])

                #updates in gcm db
                old_device = GCMDevice.objects.get(user=user)
                old_device.registration_id = data['gcm_token']
                old_device.active = True
                old_device.save()
                response['code'] = UPDATE_GCM_TOKEN_SUCCESS_CODE
                response['message'] = UPDATE_GCM_TOKEN_SUCCESS_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_200_OK)
            except GCMDevice.DoesNotExist as e:

                # Creates a gcmdevice object if the user is logging in for the first time 
                new_device = GCMDevice(user=user, registration_id=data['gcm_token'])
                new_device.save()

                response['code'] = UPDATE_GCM_TOKEN_NEW_DEVICE_CODE
                response['message'] = UPDATE_GCM_TOKEN_NEW_DEVICE_MESSAGE
                response['data'] = None
                return JSONResponse(response, status=status.HTTP_201_CREATED)
        else:
            error_dict = {}
            response['code'] = UPDATE_GCM_TOKEN_MISSING_FIELD_CODE
            response['message'] = UPDATE_GCM_TOKEN_MISSING_FIELD_MESSAGE
            for key, value in udpate_gcm_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

class GetUsernameAvailabilityPreLoginView(APIView):
    """
    Check whether the entered username is available or not
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    authentication_classes = (CsrfExemptSessionAuthentication, )
    lookup_url_kwarg = "username"
    def get(self, request, username):
        response = {}

        try:
            
            # Checks whether the entered username is already taken or not
            user_object = Users.objects(username=username).first()

            if user_object is None:
                response['code'] = USERNAME_AVAILABLE_CODE
                response['message'] = USERNAME_AVAILABLE_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_200_OK)
            else:
                response['code'] = USERNAME_NOT_AVAILABLE_CODE
                response['message'] = USERNAME_NOT_AVAILABLE_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            response['code'] = USERNAME_AVAILABILITIY_DATA_EXCEPTION_CODE
            response['message'] = USERNAME_AVAILABILITIY_DATA_EXCEPTION_MESSAGE + type(e).__name__
            response['data'] = None
            return Response(response, status= status.HTTP_400_BAD_REQUEST)


class LoginWithFacebookView(APIView):
    """
    Register/Logs in a user in the django auth model and in custom users database using Facebook access token
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    serializer_class = LoginWithFacebookRequestSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = LoginWithFacebookRequestSerializer(data=data)
        response = {}
        registration_object = {}

        if serializer.is_valid():
            facebook_user_id = data['user_id']
            facebook_access_token = data['access_token']

            # Create the API url, from where we have to get the data
            graph_url = "https://graph.facebook.com/" + facebook_user_id + "/?fields=first_name,last_name,email,picture&access_token=" + facebook_access_token
            
            # Hit the facebook api to get the data
            graph_response = requests.get(graph_url)

            # Convert the response into dictonary
            response_in_json = graph_response.json()

            # Extract the fields from the dictonary into custom dictonary
            striped_string = response_in_json['first_name']
            striped_string = striped_string.replace(" ","")
            registration_object['first_name'] = first_name = striped_string
            registration_object['last_name'] = last_name = response_in_json['last_name']
            registration_object['email_id'] = email_id = response_in_json['email']

            profile_data = response_in_json['picture']
            inner_data = profile_data['data']
            registration_object['profile_url'] = profile_url = inner_data['url']

            try:
                # Check whether the user is already in the database
                user_object = User.objects.get(email=email_id)
                
                # Login if the user is present
                login(request, user_object)
                
                # Get the data similar to login and send it back to the user
                token, created = Token.objects.get_or_create(user=user_object)
                user_data = Users.objects.get(username=user_object.username)
                user_data.token = token
                serialized_data = UsersSerializer(user_data)

                response['code'] = LOGIN_WITH_FB_SUCCESS_CODE
                response['data'] = serialized_data.data
                response['message']= LOGIN_WITH_FB_SUCCESS_MESSAGE + user_object.username + '!'
                return JSONResponse(response, status=status.HTTP_200_OK)

            except User.DoesNotExist as e:
                # If the user does not exist, create a new record for that user in database
                # Generate a random userid, username and password for the new user

                photo_url = "https://graph.facebook.com/" + facebook_user_id + "/picture?width=480&height=480&access_token=" + facebook_access_token
                
                registration_object['user_id'] = userid = str(uuid.uuid4())
                number = '{:03d}'.format(random.randrange(1, 999))
                registration_object['username'] = username = (first_name + number)
                new_password = User.objects.make_random_password()

                # Check whether all the data got from the api is valid or not
                fb_serializer = FacebookRegistrationSerializer(data=registration_object)
                if fb_serializer.is_valid():

                    # Create user record in both databases
                    fb_serializer.save()
                    User.objects.create_user(username=username,email=email_id,password=new_password)

                    # authenticate and login the users and get the data to send it back to the user
                    user = authenticate(username=username , password=new_password)
                    login(request, user)

                    # Get and set the token
                    token, created = Token.objects.get_or_create(user=user)
                    user_data = Users.objects.get(username=username)
                    user_data.token = token
                    serialized_data = UsersSerializer(user_data)
                    response['data'] = serialized_data.data

                    # Send a mail to the user with his user credentials
                    send_mail('Rhythm App Registration', 'Your default system generated username and password are: ' + username + " and " + new_password + " respectively.\nYou can change this after logging in to the app.", 'sachinmutthe007@gmail.com', [email_id,], fail_silently=False)

                    response['code'] = LOGIN_WITH_FB_NEW_USER_CODE
                    response['data'] = serialized_data.data
                    response['message']= LOGIN_WITH_FB_NEW_USER_MESSAGE+ username + '!'
                    return JSONResponse(response, status=status.HTTP_201_CREATED)
                else:
                    response['code'] = LOGIN_WITH_FB_DATA_EXCEPTION_CODE
                    response['data'] = None
                    response['message']= LOGIN_WITH_FB_DATA_EXCEPTION_MESSAGE
                    return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            error_dict = {}
            response['code'] = LOGIN_WITH_FB_MISSING_FIELDS_CODE
            response['message'] = LOGIN_WITH_FB_MISSING_FIELDS_MESSAGE
            for key, value in serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)


class LoginWithGoogleView(APIView):
    """
    Register/Logs in a user in the django auth model and in custom users database using Google access token
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (JSONParser,)
    serializer_class = LoginWithGoogleRequestSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = LoginWithGoogleRequestSerializer(data=data)
        response = {}
        registration_object = {}

        if serializer.is_valid():
            
            google_access_token = data['access_token']

            # Create a header for passing the access token to the API
            header = "Bearer " + google_access_token

            # API url to get the user's data
            google_url = "https://www.googleapis.com/plus/v1/people/me"

            # Hit the api and get the respose in dict
            google_response = requests.get(google_url, headers={'Authorization': header})
            response_in_json = google_response.json()

            # Extract the sub dictionaries
            name_dict = response_in_json['name']
            emails_list = response_in_json['emails']
            image_data = response_in_json['image']

            # Create a data dictionary for the values extracted from the response
            striped_string = name_dict['givenName']
            striped_string = striped_string.replace(" ","")
            registration_object['first_name'] = first_name = striped_string
            registration_object['last_name'] = last_name = name_dict['familyName']
            registration_object['email_id'] = email_id = emails_list[0]['value']
            registration_object['profile_url'] = profile_url = image_data['url'].replace("50","500")

            try:
                # Check whether the user is a new user or a returning user
                user_object = User.objects.get(email=email_id)
                
                # If the user is returning user then get the data from both the databases and return it back
                login(request, user_object)
                
                # Returns data similar to login API
                token, created = Token.objects.get_or_create(user=user_object)
                user_data = Users.objects.get(username=user_object.username)
                user_data.token = token
                serialized_data = UsersSerializer(user_data)

                response['code'] = LOGIN_WITH_GOOGLE_SUCCESS_CODE
                response['data'] = serialized_data.data
                response['message']= LOGIN_WITH_GOOGLE_SUCCESS_MESSAGE + user_object.username + '!'
                return JSONResponse(response, status=status.HTTP_200_OK)

            except User.DoesNotExist as e:
                # If the user does not exist, create a new record for that user in database

                # Generate new userid, username and password for the new user
                registration_object['user_id'] = userid = str(uuid.uuid4())
                number = '{:03d}'.format(random.randrange(1, 999))
                # Generates a username with first_name and random 6 digit number
                registration_object['username'] = username = (first_name + number)
                new_password = User.objects.make_random_password()

                # Check whether all the data got from the api is valid or not
                google_serializer = GoogleRegistrationSerializer(data=registration_object)
                if google_serializer.is_valid():

                    # Create user record in both databases
                    google_serializer.save()
                    User.objects.create_user(username=username,email=email_id,password=new_password)

                    # authenticate and login the users and get the data to send it back to the user
                    user = authenticate(username=username , password=new_password)
                    login(request, user)

                    token, created = Token.objects.get_or_create(user=user)
                    user_data = Users.objects.get(username=username)
                    user_data.token = token
                    serialized_data = UsersSerializer(user_data)
                    response['data'] = serialized_data.data

                    # Send a mail to the user with his user credentials
                    send_mail('Rhythm App Registration', 'Your default system generated username and password are: ' + username + " and " + new_password + " respectively.\nYou can change this after logging in to the app.", 'sachinmutthe007@gmail.com', [email_id,], fail_silently=False)

                    response['code'] = LOGIN_WITH_GOOGLE_NEW_USER_CODE
                    response['data'] = serialized_data.data
                    response['message']= LOGIN_WITH_GOOGLE_NEW_USER_MESSAGE + username + '!'
                    return JSONResponse(response, status=status.HTTP_201_CREATED)
                else:
                    response['code'] = LOGIN_WITH_GOOGLE_DATA_EXCEPTION_CODE
                    response['data'] = None
                    response['message']= LOGIN_WITH_GOOGLE_DATA_EXCEPTION_MESSAGE
                    return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            error_dict = {}
            response['code'] = LOGIN_WITH_GOOGLE_MISSING_FIELDS_CODE
            response['message'] = LOGIN_WITH_GOOGLE_MISSING_FIELDS_MESSAGE
            for key, value in serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return JSONResponse(response, status=status.HTTP_400_BAD_REQUEST)

class DeleteUserView(APIView):
    """
    Report a post and related data
    """

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = DeleteUserSerializer

    def post(self, request):
        response = {}
        data = JSONParser().parse(request)
        delete_serializer = DeleteUserSerializer(data=data)

        if delete_serializer.is_valid():

            user_id = delete_serializer.validated_data['user_id']

            try:

                user = Users.objects.get(user_id=user_id)

                # remove from followers
                if len(user.followed_users_list) > 0:
                    for followed_user in user.followed_users_list:

                        Users.objects(user_id=followed_user.user_id).update_one(
                            pull__follower_users_list__user_id=user_id,
                            pull__notifications__notification_id=followed_user.notification_id)

                # remove from following
                if len(user.follower_users_list) > 0:
                    for follower in user.follower_users_list:
                                    
                        Users.objects(user_id=follower.user_id).update_one(
                            pull__followed_users_list__user_id=user_id,
                            pull__notifications__notification_id=follower.notification_id)

                # remove posts
                RhythmPosts.objects(user_id=user_id).delete()

                # delete user
                user.delete()

                response['code'] = DELETE_USER_SUCCESS_CODE
                response['message']= DELETE_USER_SUCCESS_MESSAGE
                response['data'] = None

                return JSONResponse(response, status=status.HTTP_200_OK)

            except Exception as e:

                print (e)
                response['code'] = DELETE_USER_DATA_EXCEPTION_CODE
                response['message'] = DELETE_USER_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)
        else:
            error_dict = {}
            response['code'] = DELETE_USER_MISSING_FIELDS_CODE
            response['message'] = DELETE_USER_MISSING_FIELDS_MESSAGE
            for key, value in delete_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)            