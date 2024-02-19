from rest_framework import response, viewsets, status, response
from order.models import AssignOrder
from order.serializers import AssignOrderSerializer


class AssignOrderView(viewsets.ModelViewSet):
   queryset = AssignOrder.objects.prefetch_related("order")
   serializer_class = AssignOrderSerializer