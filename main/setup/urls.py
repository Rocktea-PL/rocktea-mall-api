from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from mall.views import CreateStoreOwner, GetCategories, CreateStore, ProductViewSet, UploadProductImage, MarketPlaceView, ProductVariantView, StoreProductVariantView
from order.views import OrderItemsViewSet, OrderViewSet
from tenants.views import TenantSignUp
from django.urls import path

# def trigger_error(request):
#     division_by_zero = 1 / 0


router = routers.DefaultRouter()
router.register('storeowner', CreateStoreOwner, basename="user")
router.register('categories', GetCategories, basename='categories')
router.register('create/store', CreateStore, basename='create-store')
router.register('signup/user', TenantSignUp, basename="signup-tenant")
router.register('products', ProductViewSet, basename='products')
router.register('marketplace', MarketPlaceView, basename='marketplace')
router.register('product-variant', ProductVariantView, basename='productvariant')
router.register('store-variant', StoreProductVariantView, basename='store-variant')
router.register(r'orderitems', OrderItemsViewSet, basename='orderitems')
router.register('orders', OrderViewSet, basename='orders')
# router.register('upload-image', UploadProductImage, basename="product-image")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('rocktea/', include(router.urls)),
    path('mall/', include("mall.urls")),
    path('store/', include("tenants.urls")),
    path('dropshippers/', include('dropshippers.urls')),
    path('order/', include('order.urls')),
    # path('sentry-debug/', trigger_error),
]
