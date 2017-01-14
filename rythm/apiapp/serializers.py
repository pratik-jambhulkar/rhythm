from rest_framework import serializers
from apiapp.models import *
from rest_framework_mongoengine.serializers import DocumentSerializer, EmbeddedDocumentSerializer
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class UsersSerializer(DocumentSerializer):
    class Meta:
        model = Users
        depth = 1
        exclude = ('id','notifications','followed_users_list','follower_users_list','pending_requests','requested_users',)

class RegistrationSerializer(DocumentSerializer):

    class Meta:
        """docstring for Meta"""
        model = Users
        depth = 1
        fields = ('user_id','username', 'first_name', 'last_name', 'email_id'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Users.objects.all(),
                fields=('user_id','username', 'email_id')
            )
        ]

class LoginSerializer(DocumentSerializer):
    """docstring for LoginSerializer"""
    class Meta:
        model = LoginDetails
        fields = ('username','password', )

class ForgotPasswordSerializer(DocumentSerializer):
    class Meta:
        model = ForgotPassword
        fields = ('email_id',)

class LogoutSerializer(DocumentSerializer):
    class Meta:
        model = Logout
        fields = ('user_id',)

class UpdateGCMRequestSerializer(DocumentSerializer):
    class Meta:
        model = UpdateGCMRequest
        fields = ('gcm_token', 'user_id',)

class LoginWithFacebookRequestSerializer(DocumentSerializer):
    class Meta:
        model = LoginWithFacebookRequest
        fields = ('user_id', 'access_token',)

class FacebookRegistrationSerializer(DocumentSerializer):

    class Meta:
        """docstring for Meta"""
        model = Users
        depth = 1
        fields = ('user_id','username', 'first_name', 'last_name', 'email_id','profile_url',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Users.objects.all(),
                fields=('user_id','username', 'email_id')
            )
        ]

class LoginWithGoogleRequestSerializer(DocumentSerializer):
    class Meta:
        model = LoginWithGoogleRequest
        fields = ('access_token',)


class GoogleRegistrationSerializer(DocumentSerializer):

    class Meta:
        """docstring for Meta"""
        model = Users
        depth = 1
        fields = ('user_id','username', 'first_name', 'last_name', 'email_id','profile_url',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Users.objects.all(),
                fields=('user_id','username', 'email_id')
            )
        ]

class UserBasicInfoSerializer(DocumentSerializer):
    class Meta:
        model = UpdateBasicInfo
        exclude = ('id',)

class FollowRequestSerializer(serializers.Serializer):
	source_user_id = serializers.CharField(max_length=36,required=True)
	target_user_id = serializers.CharField(max_length=36,required=True)