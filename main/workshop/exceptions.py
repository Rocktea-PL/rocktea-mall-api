from rest_framework.exceptions import APIException


class CustomException(APIException):
   status_code = 400
   default_detail = "Dang! Something just broke!"
   
   def __init__(self, detail=None):
      if detail is not None:
         self.detail=detail
      else:
         self.detail = self.default_detail


class ValidationError(CustomException):
   status_code = 400
   default_detail = 'Validation Error'


class AuthenticationFailedError(CustomException):
   status_code = 401
   default_detail = 'Authentication Failed'


class NotFoundError(CustomException):
   status_code = 404
   default_detail = 'Not Found'
   

class InternalServerError(CustomException):
   status_code = 500
   default_detail = 'Internal Server Error'
