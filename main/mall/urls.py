from django.urls import path
from .views import SignInUserView, Check
from .payments import OTP

urlpatterns = [
    path("signin/", SignInUserView.as_view(), name="signin"),
    path("otp_payment/", OTP.StoreOTPPayment.as_view(), name="otp_payment"),
    path("verify/", OTP.VerifyPayment.as_view(), name="verify-transaction"),
    path("check-user", Check.as_view(), name="check")
]
