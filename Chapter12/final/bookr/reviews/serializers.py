from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

from .models import Book, Publisher, Review
from .utils import average_rating


class PublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = ['pk', 'name', 'website', 'email']


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email']


class BookSerializer(serializers.ModelSerializer):
    publisher = PublisherSerializer()
    rating = serializers.SerializerMethodField('book_rating')
    reviews = serializers.SerializerMethodField('book_reviews')

    def book_rating(self, book):
        reviews = book.review_set.all()
        if reviews:
            return average_rating([review.rating for review in reviews])

    def book_reviews(self, book):
        reviews = book.review_set.all()
        if reviews:
            return ReviewSerializer(reviews, many=True).data

    class Meta:
        model = Book
        fields = ['pk', 'title', 'publication_date', 'isbn', 'publisher', 'rating', 'reviews']


class ReviewSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    book = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['pk', 'content', 'date_created', 'date_edited', 'rating', 'creator', 'book', 'book_id']

    def create(self, validated_data):
        request = self.context['request']
        creator = request.user
        book = Book.objects.get(pk=request.data['book_id'])
        return Review.objects.create(content=validated_data['content'], book=book, creator=creator,
                                     rating=validated_data['rating'])

    def update(self, instance, validated_data):
        request = self.context['request']
        creator = request.user
        if instance.creator_id != creator.pk:
            raise PermissionDenied('Permission denied, you are not the creator of this review')
        instance.content = validated_data['content']
        instance.rating = validated_data['rating']
        instance.date_edited = timezone.now()
        instance.save()
        return instance

