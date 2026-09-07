from django.urls import path
from . import views
from .views import (
    add_to_wishlist,
    remove_from_wishlist,
)


urlpatterns = [

    # =====================================================
    # CUSTOMER
    # =====================================================

    path(
        'customer/',
        views.customer_dashboard,
        name='customer_dashboard'
    ),

    
    path(
    "customer/profile/",
    views.customer_profile,
    name="customer_profile"
    ),


    path(
    'customer/orders/',
    views.customer_orders,
    name='customer_orders'
    ),
    
    path(
    'customer/cart/',
    views.customer_cart,
    name='customer_cart'
    ),

    path(
    'customer/wishlist/',
    views.customer_wishlist,
    name='customer_wishlist'
    ),

    path(
    'customer/cart/add/<int:product_id>/',
    views.add_to_cart,
    name='add_to_cart'
    ),
    path(
    'cart/increase/<int:item_id>/',
    views.increase_cart_quantity,
    name='increase_cart_quantity'
    ),

    path(
    'cart/decrease/<int:item_id>/',
    views.decrease_cart_quantity,
    name='decrease_cart_quantity'
    ),
    path(
    'customer/cart/remove/<int:item_id>/',
    views.remove_cart_item,
    name='remove_cart_item'
    ),
    path(
    'customer/checkout/',
    views.checkout,
    name='checkout'
    ),

    path(
    'customer/place-order/',
    views.place_order,
    name='place_order'
     ),

    path(
    'orders/cancel/<int:item_id>/',
    views.cancel_order_item,
    name='cancel_order_item'
    ),
    path(
    'customer/wishlist/add/<int:product_id>/',
    views.add_to_wishlist,
    name='add_to_wishlist'
    ),

    path(
    'customer/wishlist/remove/<int:product_id>/',
    views.remove_from_wishlist,
    name='remove_from_wishlist'
    ),

    path(
    'customer/review/<int:product_id>/',
    views.add_review,
    name='add_review'
    ),
    




    # =====================================================
    # VENDOR
    # =====================================================

    path(
        'vendor/',
        views.vendor_dashboard,
        name='vendor_dashboard'
        
    ),

    path(
        'vendor/add-product/',
        views.add_product,
        name='add_product'
    ),

    path(
    'vendor/products/<int:product_id>/',
    views.view_product,
    name='view_product'
     ),

    path(
    'vendor/products/<int:product_id>/edit/',
    views.edit_product,
    name='edit_product'
    ),

    path(
    'vendor/products/<int:product_id>/delete/',
    views.delete_product,
    name='delete_product'
     ),

    path(
    'vendor/profile/',
    views.vendor_profile,
    name='vendor_profile'
    ),

    path(
    'vendor/orders/',
    views.vendor_orders,
    name='vendor_orders'
    ), 
    path(
    'vendor/orders/<int:item_id>/status/',
    views.update_vendor_order_status,
    name='update_vendor_order_status'
    ),
    path(
    'vendor/notifications/',
    views.vendor_notifications,
    name='vendor_notifications'
   ),
   path(
    'vendor/notifications/<int:notification_id>/',
    views.open_vendor_notification,
    name='open_vendor_notification'
    ),

    path(
    'vendor/notifications/clear/',
    views.clear_vendor_notifications,
    name='clear_vendor_notifications'
    ),


    # =====================================================
    # ADMIN
    # =====================================================

    path(
        'admin/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin/users/',
        views.view_users,
        name='view_users'
    ),

    path(
        'admin/users/<int:user_id>/edit/',
        views.edit_user,
        name='edit_user'
    ),

    path(
        'admin/users/<int:user_id>/delete/',
        views.delete_user,
        name='delete_user'
    ),


    # =====================================================
    # LOGOUT
    # =====================================================

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),
]