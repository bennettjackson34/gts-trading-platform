from rest_framework import serializers
from .models import Trades
class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trades
        fields = ['id', 'asset', 'direction', 'entry_price', 'exit_price', 'risk_price', 'target_price']