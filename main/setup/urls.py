from django.urls import path, include, re_path
from django.contrib import admin
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Mall app imports
from mall.views import (
    CreateStoreOwner, GetCategories, CategoryViewSet, CreateStore,
    ProductViewSet, MarketPlaceView, ProductVariantView, ProductDetails,
    BrandView, SubCategoryView, ProductTypeView, WalletView,
    ServicesBusinessInformationView, CreateLogisticsAccount, CreateOperationsAccount,
    GetStoreDropshippers, NotificationView, PromoPlansView, BuyerBehaviourView,
    ShippingDataView, ProductReviewViewSet, DropshipperReviewViewSet,
    ProductRatingViewSet, EmailVerificationViewSet
)
from mall.change_password import ChangePasswordView
from mall.health_views import health_check
from mall.custom_view.reportuser import ReportUserView
from mall.wishlist import WishlistViewSet

# Order app imports
from order.views import (
    OrderItemsViewSet, CartViewSet, CartItemModifyView, CheckOutCart,
    ViewOrders, OrderDeliverView, AllOrders, PaymentHistoryView,
    InitiatePayment, ShipbubbleViewSet, Paystack
)
from order.logistics.assign_order import AssignOrderView

# Other app imports
from services.views import SignUpServices, ServicesCategoryView
from tenants.views import TenantSignUp, VerifyEmail

schema_view = get_schema_view(
    openapi.Info(
        title="RockTea PL API",
        default_version='v1.0',
        description="RockTea PL API: Empowering seamless integration and enhanced shopping experiences with a versatile and efficient e-commerce application programming interface.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="rockteapl1@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Router configuration for /rocktea/ endpoints
router = routers.DefaultRouter()

# User & Store Management
router.register('dropshippers/store', GetStoreDropshippers, basename="dropship")
router.register('create/store', CreateStore, basename='create-store')
router.register('signup/user', TenantSignUp, basename="signup-tenant")
router.register('signup/services', SignUpServices, basename='signup-services')
router.register('signup/logistics', CreateLogisticsAccount, basename='logistics')
router.register('signup/operations', CreateOperationsAccount, basename='operations')

# Categories & Products
router.register('categories', GetCategories, basename='categories')
router.register('category', CategoryViewSet, basename='category')
router.register('products', ProductViewSet, basename='products')
router.register('marketplace', MarketPlaceView, basename='marketplace')
router.register('product-variant', ProductVariantView, basename='productvariant')
router.register('product-details', ProductDetails, basename='product-details')
router.register('brand', BrandView, basename='brands')
router.register('subcategory', SubCategoryView, basename='subcategory')
router.register('product-type', ProductTypeView, basename='product-type')

# Reviews & Ratings
router.register('product-reviews', ProductReviewViewSet, basename='reviews')
router.register('dropshipper-review', DropshipperReviewViewSet, basename='dropshipper-reviews')
router.register('product-rating', ProductRatingViewSet, basename='rating')

# Cart & Orders
router.register('cart', CartViewSet, basename="add-to-cart")
router.register('cart-item', CartItemModifyView, basename="cartitem")
router.register('checkout', CheckOutCart, basename='checkout')
router.register('orderitems', OrderItemsViewSet, basename='orderitems')
router.register('my-orders', ViewOrders, basename="view-orders")
router.register('order-delivery/confirmation', OrderDeliverView, basename='confirmation')
router.register('assign-order', AssignOrderView, basename='assigned_orders')
router.register('all-orders', AllOrders, basename='allorders')

# Payments & Wallet
router.register('wallet', WalletView, basename='wallets')
router.register('payment/history', PaymentHistoryView, basename='payment')
router.register('payment/initialize', InitiatePayment, basename='payment-initializer')
router.register('paystack', Paystack, basename='paystack')

# Services & Business
router.register('business_info', ServicesBusinessInformationView, basename='business')
router.register('services-category', ServicesCategoryView, basename='service-cat')

# Shipping & Logistics
router.register('shipping-data', ShippingDataView, basename='shipping_data')
router.register('shipbubble', ShipbubbleViewSet, basename='shipbubble')

# User Features
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('notifications', NotificationView, basename='notifications')
router.register('buyer-behaviour', BuyerBehaviourView, basename='buyerbehavior')
router.register('report/user', ReportUserView, basename='report-user')
router.register('promo/', PromoPlansView, basename='promos')



urlpatterns = [
    # Documentation & Admin
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    
    # Main API endpoints (existing production URLs)
    path('rocktea/', include(router.urls)),
    path('mall/', include("mall.urls")),
    path('store/', include("tenants.urls")),
    path('dropshippers/', include('dropshippers.urls')),
    path('order/', include('order.urls')),
    path('service/', include('services.urls')),
    
    # API namespace
    path('api/', include([
        path('admin-management/', include('mall.admin_urls')),  # New admin management
        path('admin/products/', include('products.urls')),
        path('accounts/', include('accounts.urls')),
        path('admin/orders/', include('admin_orders.urls')),
        path('admin/', include('dashboards.urls')),
        path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    ])),
    
    # Authentication & Verification
    path('verify-email/', VerifyEmail.as_view(), name='verify-email'),
    path('resend-verification-email/', 
         EmailVerificationViewSet.as_view({'post': 'resend_verification'}), 
         name='resend-verification-email'),
    
    # Special endpoints
    re_path(r'^rocktea/storeowner/$', CreateStoreOwner.as_view({
        'get': 'list',
        'post': 'create',
        'patch': 'update_user_store'
    }), name='storeowner-list-patch'),
]

# Add router URLs (maintains existing /rocktea/ endpoints)
urlpatterns += router.urls