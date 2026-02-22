from rest_framework import serializers
from .models import ContactSubmission, Subscriber, ContactStatus, SubscriberStatus

class ContactSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["full_name", "email", "subject", "message"]

class ContactSubmissionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = [
            "id", "full_name", "email", "subject", "message",
            "status", "created_at", "updated_at",
        ]


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()

class UnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SubscriberAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = [
            "id", "email", "status",
            "subscribed_at", "unsubscribed_at",
            "created_at", "updated_at",
        ]
