from django.urls import path, re_path
from .views import (
    SignInUserView, 
    UploadProductImage, 
    DropshipperDashboardCounts, 
    StoreOrdersViewSet, 
    BestSellingProductView, 
    StoreProductPricingAPIView, 
    CreateAndGetStoreProductPricing,
    SalesCountView,
    ProductFilter,
    CustomResetPasswordRequestToken, 
    CustomResetPasswordConfirm
    )
# PaystackWebhookView,
from order.views import paystack_webhook
from .payments import OTP
from mall.store_features.product import GetVariantAndPricing
from mall.payments.verify_payment import verify_payment
from mall.payments.payouts import PayoutDropshipper

urlpatterns = [
    path("signin/", SignInUserView.as_view(), name="signin"),
    path("otp_payment/", OTP.StoreOTPPayment.as_view(), name="otp_payment"),
    path("verify/", OTP.VerifyPayment.as_view(), name="verify-transaction"),
    path("upload-image/", UploadProductImage.as_view(), name='uploadimage'),
    path("count/", DropshipperDashboardCounts.as_view(), name='data-counts'),
    path('store_order', StoreOrdersViewSet.as_view(), name="store"),
    path('best_selling', BestSellingProductView.as_view(), name="best_selling"),
    path('variant-pricing/<str:product_id>', GetVariantAndPricing.as_view(), name="pricing"),
    path('store-prices/', StoreProductPricingAPIView.as_view(), name='store-product-prices'),
    path('store_pricing/', CreateAndGetStoreProductPricing.as_view(),name='store-price'),
    path('sales_count', SalesCountView.as_view(), name='product-sales-count'),
    path('filter', ProductFilter.as_view(), name='product-filter'),
    path('verify_payment/<str:transaction_id>', verify_payment, name="payment"),
    path('payouts/', PayoutDropshipper.as_view(), name='make-payment'),
    path('webhook/paystack/', paystack_webhook, name='paystack_webhook'),
    path('password_reset/', CustomResetPasswordRequestToken.as_view(), name='password_reset'),
    # path('password_reset/confirm/<uidb64>/<token>/', CustomResetPasswordConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/confirm/<str:token>/', CustomResetPasswordConfirm.as_view(), name='password_reset_confirm'),
]