from django.urls import path
from .views import SignInUserView, UploadProductImage, DropshipperDashboardCounts
from .payments import OTP

urlpatterns = [
    path("signin/", SignInUserView.as_view(), name="signin"),
    path("otp_payment/", OTP.StoreOTPPayment.as_view(), name="otp_payment"),
    path("verify/", OTP.VerifyPayment.as_view(), name="verify-transaction"),
    path("upload-image/", UploadProductImage.as_view(), name='uploadimage'),
    path("count/", DropshipperDashboardCounts.as_view(), name='data-counts')
]