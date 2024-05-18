from django.urls import path, include
from django.contrib import admin
from rest_framework import routers

from mall.views import (
        CreateStoreOwner,
        GetCategories,
        CreateStore,
        ProductViewSet,
        MarketPlaceView,
        ProductVariantView,
        ProductDetails,
        BrandView,
        SubCategoryView,
        ProductTypeView,
        WalletView,
        # StoreProductPricing, 
        ServicesBusinessInformationView, 
        CreateLogisticsAccount,
        CreateOperationsAccount,
        GetStoreDropshippers,
        NotificationView,
        PromoPlansView,
        BuyerBehaviourView,
        ShippingDataView,
        ProductReviewViewSet,
        DropshipperReviewViewSet
)

from mall.custom_view.reportuser import ReportUserView
from order.views import (
    OrderItemsViewSet, 
    CartViewSet, 
    CartItemModifyView, 
    CheckOutCart, 
    ViewOrders, 
    OrderDeliverView, 
    AllOrders,
    PaymentHistoryView
    )

from order.logistics.assign_order import AssignOrderView
from services.views import (
    SignUpServices,
    ServicesCategoryView
    )

from tenants.views import TenantSignUp
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="RockTea Mall API",
        default_version='v1.0',
        description="RockTea Mall API: Empowering seamless integration and enhanced shopping experiences with a versatile and efficient e-commerce application programming interface.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="rockteapl1@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


router = routers.DefaultRouter()
# Store Owner

router.register('storeowner', CreateStoreOwner, basename="user")
router.register('dropshippers/store', GetStoreDropshippers, basename="dropship")

router.register('categories', GetCategories, basename='categories')

router.register('create/store', CreateStore, basename='create-store')

router.register('signup/user', TenantSignUp, basename="signup-tenant")

# Products
router.register('products', ProductViewSet, basename='products')

router.register('marketplace', MarketPlaceView, basename='marketplace')
router.register('product-variant', ProductVariantView, basename='productvariant')

router.register(r'orderitems', OrderItemsViewSet, basename='orderitems')
router.register('order-delivery/confirmation', OrderDeliverView, basename='confirmation')
router.register('my-orders', ViewOrders, basename="view-orders")


router.register('product-details', ProductDetails, basename='product-details')
router.register('product-reviews', ProductReviewViewSet, basename='reviews')
router.register('dropshipper-review', DropshipperReviewViewSet, basename='dropshipper-reviews')

router.register('cart', CartViewSet, basename="add-to-cart")
router.register('cart-item', CartItemModifyView, basename="cartitem")

router.register('brand', BrandView, basename='brands')
router.register('subcategory', SubCategoryView, basename='subcategory')
router.register('product-type', ProductTypeView, basename='product-type')
router.register('business_info', ServicesBusinessInformationView, basename='business')
router.register('checkout', CheckOutCart, basename='checkout')
router.register('buyer-behaviour', BuyerBehaviourView, basename='buyerbehavior')

# Payments
router.register(r'wallet', WalletView, basename='wallets')
router.register('payment/history', PaymentHistoryView, basename='payment')

# Services
router.register('signup/services', SignUpServices, basename='signup-services')
router.register('services-category', ServicesCategoryView,basename='service-cat')
router.register('report/user', ReportUserView, basename='report-user')

# Notification
router.register("notifications", NotificationView, basename='notifications')


# Logistics & Operations
router.register('signup/logistics', CreateLogisticsAccount, basename='logistics')
router.register('assign-order', AssignOrderView, basename='assigned_orders')
router.register('all-orders', AllOrders, basename='allorders')
router.register('signup/operations', CreateOperationsAccount, basename='operations')
router.register('promo/', PromoPlansView, basename='promos')


# ShippingData
router.register('shipping-data', ShippingDataView, basename='shipping_data')



urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger',cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('rocktea/', include(router.urls)),
    path('mall/', include("mall.urls")),
    path('store/', include("tenants.urls")),
    path('dropshippers/', include('dropshippers.urls')),
    path('order/', include('order.urls')),
    path('service/', include('services.urls'))
]

urlpatterns += router.urls
