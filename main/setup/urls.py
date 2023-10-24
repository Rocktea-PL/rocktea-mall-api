from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from mall.views import CreateStoreOwner, GetCategories, CreateStore, ProductViewSet, SizeViewSet, PriceViewSet, UploadProductImage, MarketPlaceView, AddStoreProductProfit
from tenants.views import TenantSignUp

router = routers.DefaultRouter()
router.register('storeowner', CreateStoreOwner, basename="user")
router.register('categories', GetCategories, basename='categories')
router.register('create/store', CreateStore, basename='create-store')
router.register('signup/user', TenantSignUp, basename="signup-tenant")
router.register('products', ProductViewSet, basename='products')
router.register('sizes', SizeViewSet, basename='product-size')
router.register(r'prices', PriceViewSet, basename='product-size')
router.register('marketplace', MarketPlaceView, basename='marketplace')
router.register('add/profit', AddStoreProductProfit, basename='profit')
# router.register('upload-image', UploadProductImage, basename="product-image")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('rocktea/', include(router.urls)),
    path('mall/', include("mall.urls")),
    path('store/', include("tenants.urls")),
    path('dropshippers/', include('dropshippers.urls')),
    path('order/', include('order.urls'))
]
