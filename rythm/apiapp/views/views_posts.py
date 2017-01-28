from rest_framework import viewsets, authentication
from apiapp.serializers import *
from apiapp.models import Users, RhythmPosts, CommentDetails
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
import uuid
from utils import get_post_details, is_post_liked, has_user_commented, get_notification_id
from datetime import datetime

class CreateANewPostView(APIView):
    """
    Creates a new Post
    """
    throttle_classes = ()
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = CreatePostSerializer

    def post(self, request):
        data = JSONParser().parse(request)
        post_serializer = CreatePostSerializer(data=data)
        response = {}

        # Check whether the data provided is valid
        if post_serializer.is_valid():

            user_id = post_serializer.validated_data['user_id']
            poster_url = post_serializer.validated_data['poster_url']
            is_comment_allowed = post_serializer.validated_data['is_comment_allowed']
            post_caption = post_serializer.validated_data['post_caption']
            song_name = post_serializer.validated_data['song_name']
            album = post_serializer.validated_data['album']
            ratings = post_serializer.validated_data['ratings']

            try:
                # Create a post id for the new post
                post_id = str(uuid.uuid4())

                # Create a post object according to the data passed to the API
                new_post_object = RhythmPosts(post_id=post_id,
                    user_id=user_id,
                    poster_url= poster_url,
                    is_comment_allowed= is_comment_allowed,
                    post_caption= post_caption, 
                    song_name= song_name,
                    album= album,
                    ratings= ratings)

                # Save the new post
                new_post_object.save()

                # Get the new object
                post_object = RhythmPosts.objects.get(post_id=post_id)

                # Get the details of the post in a dictionary to return it
                post_data = get_post_details(post_object)

                response['code'] = POST_CREATE_SUCCESS_CODE
                response['message'] = POST_CREATE_SUCCESS_MESSAGE
                response['data'] = post_data
                return Response(response, status=status.HTTP_201_CREATED)

            except Exception as e:

                print (e)

                response['code'] = POST_CREATE_DATA_EXCEPTION_CODE
                response['message'] = POST_CREATE_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            error_dict = {}
            response['code'] = POST_CREATE_MISSING_FIELDS_CODE
            response['message'] = POST_CREATE_MISSING_FIELDS_MESSAGE
            for key, value in sc_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class LikePostView(APIView):
    """
    Likes/unlikes a post depending the method type
    """

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = LikeSerializer

    def post(self, request):
        response = {}
        data = JSONParser().parse(request)
        like_serializer = LikeSerializer(data=data)

        if like_serializer.is_valid():

            user_id = like_serializer.validated_data['user_id']
            post_id = like_serializer.validated_data['post_id']

            try:

                # Get the post object for the particular post id
                post_object = RhythmPosts.objects.get(post_id=post_id)

                post_owner_id = post_object.user_id

                # Check whether the user has already liked the post or not
                if not is_post_liked(user_id,post_object):

                    # Create a notification object for the post
                    notification_id = str(uuid.uuid4())
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    notification_details = NotificationDetails(_id=post_id, image_url=post_object.poster_url)
                    notification_object = Notifications(user_id = user_id, notification_id = notification_id,
                        notification_type = 3, 
                        notification_details = notification_details)

                    # Push the notification object created for this user
                    Users.objects(user_id=post_owner_id).update_one(
                        push__notifications=notification_object,
                        set__is_unread_notification=True)

                    # Insert the like object in the post details and increment the total like for that post
                    RhythmPosts.objects(post_id=post_id).update_one(
                        push__post_likes={'user_id':user_id,'notification_id':notification_id},
                        inc__total_likes=1)

                    # Get the updated likes count to send back to the user
                    updated_post = RhythmPosts.objects(post_id=post_id).only('total_likes').first()

                    response_data = {}
                    response_data['total_likes'] = updated_post.total_likes

                    response['code'] = POST_LIKE_SUCCESS_CODE
                    response['message'] = POST_LIKE_SUCCESS_MESSAGE
                    response['data'] = response_data
                    return Response(response, status= status.HTTP_200_OK)

                else:

                    response['code'] = POST_LIKE_ALREADY_LIKED_ERROR_CODE
                    response['message'] = POST_LIKE_ALREADY_LIKED_ERROR_MESSAGE
                    response['data'] = None
                    return Response(response, status= status.HTTP_400_BAD_REQUEST)

            except Exception as e:

                print (e)
                response['code'] = POST_LIKE_DATA_EXCEPTION_CODE
                response['message'] = POST_LIKE_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)
        else:
            error_dict = {}
            response['code'] = POST_LIKE_MISSING_FIELDS_CODE
            response['message'] = POST_LIKE_MISSING_FIELDS_MESSAGE
            for key, value in like_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        response = {}
        data = JSONParser().parse(request)
        unlike_serializer = LikeSerializer(data=data)

        if unlike_serializer.is_valid():

            user_id = unlike_serializer.validated_data['user_id']
            post_id = unlike_serializer.validated_data['post_id']

            try:
                # Get the post object for the particular post id
                post_object = RhythmPosts.objects.get(post_id=post_id)

                post_owner_id = post_object.user_id

                # Check whether the user has already liked the post or not
                if is_post_liked(user_id,post_object):

                    # Get the notification id for the user who wants to remove his like
                    for like_object in post_object.post_likes:
                        if like_object.user_id == user_id:
                            notification_id = like_object.notification_id

                    if notification_id is not None:
                        # Push the notification object created for this user
                        Users.objects(user_id=post_owner_id).update_one(
                            pull__notifications__notification_id=notification_id
                        )

                    # Insert the like object in the post details and increment the total like for that post
                    RhythmPosts.objects(post_id=post_id).update_one(
                        pull__post_likes__user_id=user_id,
                        dec__total_likes=1)

                    # Get the updated likes count to send back to the user
                    updated_post = RhythmPosts.objects(post_id=post_id).only('total_likes').first()

                    response_data = {}
                    response_data['total_likes'] = updated_post.total_likes

                    response['code'] = POST_UNLIKE_SUCCESS_CODE
                    response['message'] = POST_UNLIKE_SUCCESS_MESSAGE
                    response['data'] = response_data
                    return Response(response, status= status.HTTP_200_OK)

                else:

                    response['code'] = POST_UNLIKE_NOT_LIKED_ERROR_CODE
                    response['message'] = POST_UNLIKE_NOT_LIKED_ERROR_MESSAGE
                    response['data'] = None
                    return Response(response, status= status.HTTP_400_BAD_REQUEST)

            except Exception as e:

                print (e)
                response['code'] = POST_UNLIKE_DATA_EXCEPTION_CODE
                response['message'] = POST_UNLIKE_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)

        else:
            error_dict = {}
            response['code'] = POST_UNLIKE_MISSING_FIELDS_CODE
            response['message'] = POST_UNLIKE_MISSING_FIELDS_MESSAGE
            for key, value in unlike_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CommentPostView(APIView):
    """
    Add/Delete comment a post depending the method type
    """

    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    serializer_class = CommentSerializer

    def post(self, request):
        response = {}
        data = JSONParser().parse(request)
        comment_serializer = CommentSerializer(data=data)

        if comment_serializer.is_valid():

            user_id = comment_serializer.validated_data['user_id']
            post_id = comment_serializer.validated_data['post_id']
            comment = comment_serializer.validated_data['comment']

            try:

                # Get the post object for the particular post id
                post_object = RhythmPosts.objects.get(post_id=post_id)

                if post_object.is_comment_allowed:

                    post_owner_id = post_object.user_id

                    # Create a notification object for the post
                    notification_id = str(uuid.uuid4())
                    comment_id = str(uuid.uuid4())

                    comment_details = CommentDetails(comment_id=comment_id,
                        notification_id=notification_id,
                        comment=comment,
                        user_id=user_id)

                    notification_details = NotificationDetails(_id=comment_id, 
                        image_url=post_object.poster_url,
                        title=comment)
                    notification_object = Notifications(user_id = user_id, notification_id = notification_id,
                        notification_type = 4, 
                        notification_details = notification_details)

                    # Push the notification object created for this user
                    Users.objects(user_id=post_owner_id).update_one(
                        push__notifications=notification_object,
                        set__is_unread_notification=True)

                    # Insert the like object in the post details and increment the total like for that post
                    RhythmPosts.objects(post_id=post_id).update_one(
                        push__post_comments=comment_details,
                        inc__total_comments=1)

                    # Get the updated likes count to send back to the user
                    updated_post = RhythmPosts.objects(post_id=post_id).only('total_comments').first()

                    response_data = {}
                    response_data['total_comments'] = updated_post.total_comments

                    response['code'] = POST_ADD_COMMENT_SUCCESS_CODE
                    response['message'] = POST_ADD_COMMENT_SUCCESS_MESSAGE
                    response['data'] = response_data
                    return Response(response, status= status.HTTP_200_OK)

                else:
                    # Comment not allowed
                    response['code'] = POST_ADD_COMMENT_NOT_ALLOWED_ERROR_CODE
                    response['message'] = POST_ADD_COMMENT_NOT_ALLOWED_ERROR_MESSAGE
                    response['data'] = None
                    return Response(response, status= status.HTTP_400_BAD_REQUEST)

            except Exception as e:

                print (e)
                response['code'] = POST_ADD_COMMENT_DATA_EXCEPTION_CODE
                response['message'] = POST_ADD_COMMENT_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)
        else:
            error_dict = {}
            response['code'] = POST_ADD_COMMENT_MISSING_FIELDS_CODE
            response['message'] = POST_ADD_COMMENT_MISSING_FIELDS_MESSAGE
            for key, value in comment_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        response = {}
        data = JSONParser().parse(request)
        comment_serializer = CommentSerializer(data=data)

        if comment_serializer.is_valid():

            user_id = comment_serializer.validated_data['user_id']
            post_id = comment_serializer.validated_data['post_id']
            comment_id = comment_serializer.validated_data['comment']

            try:
                # Get the post object for the particular post id
                post_object = RhythmPosts.objects.get(post_id=post_id)

                post_owner_id = post_object.user_id

                is_user_comment = has_user_commented(user_id, comment_id,post_object.post_comments)

                if user_id == post_owner_id or is_user_comment:
                    # Delete Post
                    notification_id = get_notification_id(comment_id, post_object.post_comments)

                    post_object.update(pull__post_comments__comment_id=comment_id,
                        dec__total_comments=1)

                    Users.objects.get(user_id=post_owner_id).update(pull__notifications__notification_id=notification_id)
                    
                    # Get the updated likes count to send back to the user
                    updated_post = RhythmPosts.objects(post_id=post_id).only('total_comments').first()

                    response_data = {}
                    response_data['total_comments'] = updated_post.total_comments

                    response['code'] = POST_DELETE_COMMENT_SUCCESS_CODE
                    response['message'] = POST_DELETE_COMMENT_SUCCESS_MESSAGE
                    response['data'] = response_data
                    return Response(response, status= status.HTTP_200_OK)
                else:

                    response['code'] = POST_DELETE_COMMENT_NOT_AUTHORISED_CODE
                    response['message'] = POST_DELETE_COMMENT_NOT_AUTHORISED_MESSAGE
                    response['data'] = None
                    return Response(response, status= status.HTTP_400_BAD_REQUEST)

            except Exception as e:

                print (e)
                response['code'] = POST_DELETE_COMMENT_DATA_EXCEPTION_CODE
                response['message'] = POST_DELETE_COMMENT_DATA_EXCEPTION_MESSAGE
                response['data'] = None
                return Response(response, status= status.HTTP_400_BAD_REQUEST)

        else:
            error_dict = {}
            response['code'] = POST_DELETE_COMMENT_MISSING_FIELDS_CODE
            response['message'] = POST_DELETE_COMMENT_MISSING_FIELDS_MESSAGE
            for key, value in unlike_serializer.errors.items():
                error_dict[key] = value[0]
            response['data'] = error_dict
            return Response(response, status=status.HTTP_400_BAD_REQUEST)