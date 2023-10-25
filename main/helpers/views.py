from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

class BaseView(APIView):
   required_get_fields = []
   required_post_fields = []
   required_put_fields = []
   def get(self, request, format=None):
      for field in self.required_get_fields:
         if not request.GET.get(field):
               res = {
                  "code":400,
                  "message": f"{field} is required"
               }
               return Response(res,400)
      for field in self.required_post_fields:
         if not request.data.get(field):
               res = {
                  "code":400,
                  "message": f"{field} is required"
               }
               return Response(res,400)
   
   def post(self, request, format=None):
      for field in self.required_post_fields:
         if not request.data.get(field):
               res = {
                  "code":400,
                  "message": f"{field} is required"
               }
               return Response(res,400)
   
   def validate_put_request(self, request, format=None):
      for field in self.required_put_fields:
         if not field in request.data:
               res = {
                  "code": 400,
                  "message": f"{field} is required"
               }
               return Response(res, 400)
   
   def base_response(self):
      return {
         "code":200,
         "message":"success",
      }