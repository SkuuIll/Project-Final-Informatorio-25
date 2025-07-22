"""
Serializadores para la API de posts.
"""
from rest_framework import serializers
from .models import Post, Comment
from django.contrib.auth.models import User
from taggit.serializers import (TagListSerializerField,
                               TaggitSerializer)

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo User.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['email']

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Comment.
    """
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'active', 'likes_count']
        read_only_fields = ['author', 'created_at', 'likes_count']
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def create(self, validated_data):
        # Asignar el autor actual
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Serializador para el modelo Post.
    """
    author = UserSerializer(read_only=True)
    tags = TagListSerializerField()
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'created_at', 'author',
            'status', 'views', 'tags', 'comments', 'likes_count',
            'comments_count', 'favorites_count', 'reading_time', 'is_sticky'
        ]
        read_only_fields = [
            'author', 'created_at', 'views', 'likes_count',
            'comments_count', 'favorites_count', 'reading_time'
        ]
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(active=True).count()
    
    def get_favorites_count(self, obj):
        return obj.favorites.count()
    
    def create(self, validated_data):
        # Extraer tags
        tags = validated_data.pop('tags', [])
        
        # Asignar el autor actual
        validated_data['author'] = self.context['request'].user
        
        # Crear el post
        post = Post.objects.create(**validated_data)
        
        # Asignar tags
        for tag in tags:
            post.tags.add(tag)
        
        return post
    
    def update(self, instance, validated_data):
        # Extraer tags
        tags = validated_data.pop('tags', None)
        
        # Actualizar el post
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar tags si se proporcionaron
        if tags is not None:
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)
        
        instance.save()
        return instance