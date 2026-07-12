from rest_framework import serializers
from django.utils import timezone

class CWDataV2Serializer(serializers.Serializer):
    weight = serializers.DecimalField(max_digits=10, decimal_places=2) 
    product_status = serializers.ChoiceField(choices=['overweight', 'underweight', 'pass'], default='underweight')
    sku_name = serializers.CharField(max_length=12)
    client_code = serializers.IntegerField()
    sku_code = serializers.CharField(max_length=6)
    fact_code = serializers.CharField(max_length=6)
    line_no = serializers.IntegerField()
    batch_no = serializers.CharField(max_length=10)
    timestamp = serializers.DateTimeField(default=timezone.now)
