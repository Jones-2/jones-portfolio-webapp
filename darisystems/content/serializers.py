from rest_framework import serializers
from common.models import Tag, TagScope, PublishStatus
from .models import Post, PostTagMap

class PostReadSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "excerpt", "content",
            "status", "published_at", "created_at", "updated_at",
            "tags",
        ]

    def get_tags(self, obj):
        return [{"name": t.name, "slug": t.slug} for t in obj.tags.all()]


class PostWriteSerializer(serializers.ModelSerializer):
    # accept tag slugs
    tags = serializers.ListField(
        child=serializers.SlugField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Post
        fields = ["title", "slug", "excerpt", "content", "status", "published_at", "tags"]

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", None))
        published_at = attrs.get("published_at", getattr(self.instance, "published_at", None))
        if status == PublishStatus.PUBLISHED and not published_at:
            raise serializers.ValidationError({"published_at": "published_at is required when status is PUBLISHED."})
        return attrs

    def _set_tags(self, post: Post, tag_slugs: list[str]):
        tags = list(Tag.objects.filter(scope=TagScope.POST, slug__in=tag_slugs))
        PostTagMap.objects.filter(post=post).delete()
        PostTagMap.objects.bulk_create([PostTagMap(post=post, tag=t) for t in tags])
        post.tags.set(tags)

    def create(self, validated_data):
        tag_slugs = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        self._set_tags(post, tag_slugs)
        return post

    def update(self, instance, validated_data):
        tag_slugs = validated_data.pop("tags", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if tag_slugs is not None:
            self._set_tags(instance, tag_slugs)
        return instance
