from rest_framework import serializers

class CurrentIndicatorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    value = serializers.FloatField(allow_null=True)
    comment = serializers.CharField(allow_null=True)


class IndicatorUpdateItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

class HistoryIndicatorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    value = serializers.FloatField()
    comment = serializers.CharField(allow_null=True)


class HistoryPeriodSerializer(serializers.Serializer):
    period = serializers.DateField()
    indicators = HistoryIndicatorSerializer(many=True)