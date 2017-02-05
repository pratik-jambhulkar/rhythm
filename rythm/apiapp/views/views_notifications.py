from rest_framework import viewsets, authentication
from apiapp.serializers import *
from apiapp.models import Users
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from response_codes_messages import *


class GetNotificationsView(generics.ListAPIView):
    """
    Get the list of notifications of a particular user
    """

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    lookup_url_kwarg = "user_id"
    def get(self, request, user_id):
        response = {}

        try:

            # Get the notifications for a particular user
            user = Users.objects(user_id=user_id).only('notifications').first()
            notifications = user.notifications

            notifications_list = []

            # Iterate over the notifications
            for notification in notifications:

                if (notification.notification_type == 3 or notification.notification_type == 4) and notification.user_id == user_id:
                    continue

                current_id = notification.user_id
                notification_details_dict = {}
                b_user = Users.objects(user_id=current_id).only('profile_url','username').first()

                # Create the notification object
                notification_details_dict['user_id'] = current_id
                notification_details_dict['username'] = b_user.username
                notification_details_dict['profile_url'] = b_user.profile_url
                notification_details_dict['notification_type'] = notification.notification_type
                notification_details_dict['notification_received_at'] = notification.notification_received_at
                notification_details_dict['notification_id'] = notification.notification_id

                notification_details = {}
                if notification.notification_details:
                    if notification.notification_details._id:
                        notification_details['_id'] = notification.notification_details._id
                    if notification.notification_details.image_url:
                        notification_details['image_url'] = notification.notification_details.image_url
                    if notification.notification_details.title:
                        notification_details['title'] = notification.notification_details.title
                    if notification.notification_details.description:
                        notification_details['description'] = notification.notification_details.description

                    notification_details_dict['notification_details'] = notification_details

                # Append the object to the list
                notifications_list.append(notification_details_dict)

            # Sort the list according to the time at which it was received
            sorted_list = sorted(notifications_list, key=lambda k: k['notification_received_at'],
            reverse=True)

            response['code'] = NOTIFICATIONS_GET_LIST_SUCCESS_CODE
            response['message'] = NOTIFICATIONS_GET_LIST_SUCCESS_MESSAGE
            response['data'] = sorted_list
            return Response(response, status= status.HTTP_200_OK)
        except Exception as e:
            response['code'] = NOTIFICATIONS_GET_LIST_INVALID_USERID_CODE
            response['message'] = NOTIFICATIONS_GET_LIST_INVALID_USERID_MESSAGE
            response['data'] = None
            return Response(response, status= status.HTTP_400_BAD_REQUEST)


class UpdateNotificationReadView(APIView):
    """
    Change read notification variable of a user
    """

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    lookup_url_kwarg = "user_id"
    def get(self, request, user_id):
        response = {}
        
        try:

            # Get the users object for the given user id
            user_object = Users.objects(user_id=user_id).only('is_unread_notification').first()

            # Get the value of unread notification flag and return to the user
            response_dict = {}
            response_dict['is_unread_notification'] = user_object.is_unread_notification
            
            response['code'] = NOTIFICATIONS_GET_READ_STATUS_SUCCESS_CODE
            response['message'] = NOTIFICATIONS_GET_READ_STATUS_SUCCESS_MESSAGE
            response['data'] = response_dict

            return Response(response, status= status.HTTP_200_OK)
        except Exception as e:
            response['code'] = NOTIFICATIONS_GET_READ_STATUS_INVALID_USERID_CODE
            response['message'] = NOTIFICATIONS_GET_READ_STATUS_INVALID_USERID_MESSAGE
            response['data'] = None
            return Response(response, status= status.HTTP_400_BAD_REQUEST)

    def post(self, request, user_id):
        response = {}
        try:

            # Get the user object and update the notification flag to false and return
            user_object = Users.objects.get(user_id=user_id)
            user_object.update(is_unread_notification=False)
            
            response['code'] = NOTIFICATIONS_UPDATE_READ_STATUS_SUCCESS_CODE
            response['message'] = NOTIFICATIONS_UPDATE_READ_STATUS_SUCCESS_MESSAGE
            response['data'] = None

            return Response(response, status= status.HTTP_200_OK)
        except Exception as e:
            response['code'] = NOTIFICATIONS_UPDATE_READ_STATUS_INVALID_USERID_CODE
            response['message'] = NOTIFICATIONS_UPDATE_READ_STATUS_INVALID_USERID_MESSAGE
            response['data'] = None
            return Response(response, status= status.HTTP_400_BAD_REQUEST)