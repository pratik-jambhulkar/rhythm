
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
                    Users.objects.get(username=username).update(is_logged_in=True)
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