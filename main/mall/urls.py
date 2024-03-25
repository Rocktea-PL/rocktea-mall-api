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
    ProductFilter
    )
from .payments import OTP
from mall.store_features.product import GetVariantAndPricing

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
    path('filter', ProductFilter.as_view(), name='product-filter')
]