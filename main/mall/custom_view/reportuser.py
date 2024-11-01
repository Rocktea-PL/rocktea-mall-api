from mall.serializers import ReportUserSerializer
from mall.models import ReportUser
from rest_framework import viewsets, response

class ReportUserView(viewsets.ModelViewSet):
   queryset = ReportUser.objects.select_related('user')
   serializer_class = ReportUserSerializer