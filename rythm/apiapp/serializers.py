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
        exclude = ('id',)

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