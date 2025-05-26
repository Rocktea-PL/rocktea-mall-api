from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.db.models import Count, Sum, Value, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from order.pagination import CustomPagination
from order.models import StoreOrder, PaystackWebhook, Product
from mall.models import CustomUser
from order.serializers import OrderSerializer

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        total_transactions_agg = PaystackWebhook.objects.filter(
            purpose='order',
            status='Success'
        ).aggregate(
            total_amount=Coalesce(Sum('total_price'), Value(0), output_field=DecimalField()),
            total_count=Coalesce(Count('id'), Value(0), output_field=IntegerField())
        )

        stats = {
            'total_transactions': total_transactions_agg,
            'total_orders': StoreOrder.objects.count(),
            'total_products': Product.objects.count(),
            'total_dropshippers': CustomUser.objects.filter(
                is_store_owner=True
            ).count()
        }

        # Get paginated orders
        orders_queryset = StoreOrder.objects.select_related(
            'buyer', 'store'
        ).order_by('-created_at')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders_queryset, request)
        
        serializer = OrderSerializer(page, many=True)
        
        return Response({
            'stats': stats,
            'orders': paginator.get_paginated_response(serializer.data).data
        }, status=status.HTTP_200_OK)