from django.urls import path
from .views import SignInUserView, UploadProductImage, ProductPrice
from .payments import OTP

urlpatterns = [
    path("signin/", SignInUserView.as_view(), name="signin"),
    path("otp_payment/", OTP.StoreOTPPayment.as_view(), name="otp_payment"),
    path("verify/", OTP.VerifyPayment.as_view(), name="verify-transaction"),
    path("upload-image/", UploadProductImage.as_view(), name='uploadimage'),
    path("get/price", ProductPrice.as_view())
    # path('marketplace/', MarketPlaceView.as_view(), name='market-place')
]