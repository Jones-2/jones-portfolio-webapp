from rest_framework import serializers
from common.models import Tag, TagScope
from .models import Asset, AssetTagMap, AssetStatus, AssetType

class AssetReadSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            "id", "title", "slug", "description",
            "asset_type", "status",
            "external_url", "download_url",
            "is_featured", "published_at",
            "created_at", "updated_at",
            "tags",
        ]

    def get_tags(self, obj):
        return [{"name": t.name, "slug": t.slug} for t in obj.tags.all()]


class AssetWriteSerializer(serializers.ModelSerializer):
    # Accept tags as list of slugs:
    # { "tags": ["cloud", "security"] }
    tags = serializers.ListField(
        child=serializers.SlugField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Asset
        fields = [
            "title", "slug", "description",
            "asset_type", "status",
            "external_url", "download_url",
            "is_featured", "published_at",
            "tags",
        ]

    def validate(self, attrs):
        asset_type = attrs.get("asset_type", getattr(self.instance, "asset_type", None))
        status = attrs.get("status", getattr(self.instance, "status", None))
        published_at = attrs.get("published_at", getattr(self.instance, "published_at", None))
        external_url = attrs.get("external_url", getattr(self.instance, "external_url", None))

        if status == AssetStatus.PUBLISHED and not published_at:
            raise serializers.ValidationError({"published_at": "published_at is required when status is PUBLISHED."})

        if asset_type == AssetType.LINK and not external_url:
            raise serializers.ValidationError({"external_url": "external_url is required for LINK assets."})

        return attrs

    def _set_tags(self, asset: Asset, tag_slugs: list[str]):
        tags = list(Tag.objects.filter(scope=TagScope.ASSET, slug__in=tag_slugs))
        AssetTagMap.objects.filter(asset=asset).delete()
        AssetTagMap.objects.bulk_create([AssetTagMap(asset=asset, tag=t) for t in tags])
        asset.tags.set(tags)

    def create(self, validated_data):
        tag_slugs = validated_data.pop("tags", [])
        asset = Asset.objects.create(**validated_data)
        self._set_tags(asset, tag_slugs)
        return asset

    def update(self, instance, validated_data):
        tag_slugs = validated_data.pop("tags", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if tag_slugs is not None:
            self._set_tags(instance, tag_slugs)
        return instance
