from rest_framework import serializers


class SummaryDataSerializer(serializers.Serializer):
    visitors = serializers.IntegerField()
    pageviews = serializers.IntegerField()
    total_visits = serializers.IntegerField()
    bounce_rate = serializers.FloatField()
    avg_duration_seconds = serializers.FloatField()
    views_per_visit = serializers.FloatField()


class SummaryResponseSerializer(serializers.Serializer):
    data = SummaryDataSerializer()
    message = serializers.CharField()


class TimeseriesEntrySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    month = serializers.DateField(required=False)
    year = serializers.DateField(required=False)
    hour = serializers.CharField(required=False)
    visitors = serializers.IntegerField()
    pageviews = serializers.IntegerField()
    total_visits = serializers.IntegerField()
    bounce_rate = serializers.FloatField()
    avg_duration_seconds = serializers.FloatField()
    views_per_visit = serializers.FloatField()


class TimeseriesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=TimeseriesEntrySerializer())
    message = serializers.CharField()


class TopPageSerializer(serializers.Serializer):
    url = serializers.CharField()
    visitors = serializers.IntegerField()
    pageviews = serializers.IntegerField()


class PaginationMetaSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)


class TopPagesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=TopPageSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class TopReferrerSerializer(serializers.Serializer):
    source = serializers.CharField()
    medium = serializers.CharField()
    visitors = serializers.IntegerField()
    pageviews = serializers.IntegerField()


class TopReferrersResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=TopReferrerSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class CountrySerializer(serializers.Serializer):
    country = serializers.CharField()
    visitors = serializers.IntegerField()


class CountriesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=CountrySerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class DeviceSerializer(serializers.Serializer):
    device_type = serializers.CharField()
    visitors = serializers.IntegerField()


class DevicesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=DeviceSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class BrowserSerializer(serializers.Serializer):
    browser = serializers.CharField()
    visitors = serializers.IntegerField()


class BrowsersResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=BrowserSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class OSItemSerializer(serializers.Serializer):
    os = serializers.CharField()
    visitors = serializers.IntegerField()


class OSResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=OSItemSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class RegionSerializer(serializers.Serializer):
    region = serializers.CharField()
    visitors = serializers.IntegerField()


class TopRegionsResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=RegionSerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()


class CitySerializer(serializers.Serializer):
    city = serializers.CharField()
    visitors = serializers.IntegerField()


class TopCitiesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=CitySerializer())
    meta = PaginationMetaSerializer(required=False)
    message = serializers.CharField()
