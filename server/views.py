from django.http import JsonResponse
from .models import Trades
from .serializers import TradeSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(["GET","POST"])
def trade_list(request):

    if request.method == "GET":
        # get all trades
        trades = Trades.objects.all()
        # serialize them
        serializer = TradeSerializer(trades, many=True)
        return(JsonResponse(serializer.data, safe=False))
    
    if request.method == 'POST':
        print(request.data)
        # print(request.body.decode("utf-8"))

        serializer = TradeSerializer(data=request.data)

        
        if (serializer.is_valid()):
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)


