# from . import ReportUserSerializer, ReportUser
from rest_framework import viewsets, response
from mall.serializers import ReportUserSerializer
from mall.models import ReportUser

class ReportUserView(viewsets.ModelViewSet):
   queryset = ReportUser.objects.select_related('user')
   serializer_class = ReportUserSerializer