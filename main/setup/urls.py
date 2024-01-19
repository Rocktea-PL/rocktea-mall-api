from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from mall.views import CreateStoreOwner, GetCategories, CreateStore, ProductViewSet, MarketPlaceView, ProductVariantView, ProductDetails, BrandView, SubCategoryView, ProductTypeView, WalletView, StoreProductPricing, ServicesBusinessInformationView
from mall.custom_view.reportuser import ReportUserView

from order.views import OrderItemsViewSet, CartViewSet, CartItemModifyView, CheckOutCart, ViewOrders, OrderDeliverView

from services.views import SignUpServices, ServicesCategoryView
from tenants.views import TenantSignUp
from django.urls import path



router = routers.DefaultRouter()
# Store Owner
router.register('storeowner', CreateStoreOwner, basename="user")
router.register('categories', GetCategories, basename='categories')
router.register('create/store', CreateStore, basename='create-store')
router.register('signup/user', TenantSignUp, basename="signup-tenant")

# Products
router.register('products', ProductViewSet, basename='products')
router.register('marketplace', MarketPlaceView, basename='marketplace')
router.register('product-variant', ProductVariantView, basename='productvariant')
router.register('store_pricing', StoreProductPricing, basename='storeprice')
router.register(r'orderitems', OrderItemsViewSet, basename='orderitems')
router.register('order-delivery/confirmation', OrderDeliverView, basename='confirmation')

# router.register('orders', OrderViewSet, basename='orders')
router.register('product-details', ProductDetails, basename='product-details')
router.register('cart', CartViewSet, basename="add-to-cart")
router.register('cart-item', CartItemModifyView, basename="cartitem")
router.register('my-orders', ViewOrders, basename="view-orders")
router.register('brand', BrandView, basename='brands')
router.register('subcategory', SubCategoryView, basename='subcategory')
router.register('product-type', ProductTypeView, basename='product-type')
router.register('business_info', ServicesBusinessInformationView, basename='business')
router.register('checkout', CheckOutCart, basename='checkout')

# Payments
router.register('wallet', WalletView, basename='wallets')

# Services
router.register('signup/services', SignUpServices, basename='signup-services')
router.register('services-category', ServicesCategoryView,basename='service-cat')

router.register('report/user', ReportUserView, basename='report-user')




urlpatterns = [
    path('admin/', admin.site.urls),
    path('rocktea/', include(router.urls)),
    path('mall/', include("mall.urls")),
    path('store/', include("tenants.urls")),
    path('dropshippers/', include('dropshippers.urls')),
    path('order/', include('order.urls')),
    path('service/', include('services.urls'))
]
urlpatterns += router.urls
