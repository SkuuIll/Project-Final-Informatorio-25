from rest_framework import serializers
from .models import Post, Comment, User
from taggit.serializers import TagListSerializerField, TaggitSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    tags = TagListSerializerField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'header_image', 'content', 'created_at', 'author', 'slug', 'likes', 'favorites', 'tags', 'comments']
        read_only_fields = ['slug']
