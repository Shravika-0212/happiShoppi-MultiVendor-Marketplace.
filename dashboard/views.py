import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Avg, Count
from email.mime.image import MIMEImage

from .models import Product, Category,Cart,CartItem,Order,OrderItem,Payment,Notification,Wishlist,Review
from signup.models import User


# =========================================================
# ADMIN ACCESS CHECK
# =========================================================

def is_admin(request):

    return request.session.get('user_role') == 'ADMIN'


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

def customer_dashboard(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER CAN ACCESS
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    # -----------------------------------------------------
    # GET LOGGED-IN CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')


    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET CATEGORIES
    # -----------------------------------------------------

    categories = Category.objects.all().order_by(
        'category_name'
    )


    # -----------------------------------------------------
    # GET PRODUCTS
    # -----------------------------------------------------

    products = Product.objects.select_related(
    'category'
    ).annotate(
        review_count=Count('reviews'),
        average_rating=Avg('reviews__rating')
    ).order_by(
       '-id'
    )


    # -----------------------------------------------------
    # DASHBOARD CONTEXT
    # -----------------------------------------------------

    context = {

        'customer': customer,

        'categories': categories,

        'products': products,

    }


    return render(

        request,

        'dashboard/customer_dashboard.html',

        context

    )

# =========================================================
# CUSTOMER PROFILE
# =========================================================

def customer_profile(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER CAN ACCESS
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    # -----------------------------------------------------
    # GET LOGGED-IN CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')


    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # EDIT MODE
    # -----------------------------------------------------

    edit_mode = request.GET.get('edit') == 'true'


    # -----------------------------------------------------
    # SAVE PROFILE CHANGES
    # -----------------------------------------------------

    if request.method == 'POST':

        customer.name = request.POST.get(
            'name',
            customer.name
        ).strip()

        customer.phone = request.POST.get(
            'phone',
            customer.phone
        ).strip()

        customer.address = request.POST.get(
            'address',
            customer.address
        ).strip()


        customer.save(
            update_fields=[
                'name',
                'phone',
                'address'
            ]
        )


        # After saving, return to VIEW MODE

        return redirect('customer_profile')


    # -----------------------------------------------------
    # PROFILE PAGE
    # -----------------------------------------------------

    context = {

        'customer': customer,

        'edit_mode': edit_mode,

    }


    return render(

        request,

        'dashboard/customer_profile.html',

        context

    )
# =========================================================
# CUSTOMER ORDERS
# =========================================================
def customer_orders(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET CUSTOMER ORDERS
    # -----------------------------------------------------

    orders = Order.objects.filter(
        customer_id=customer_id
    ).select_related(
       'payment'
    ).prefetch_related(
        'items',
        'items__product',
        'items__vendor'
    ).order_by(
        '-created_at'
    )


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        'orders': orders,

    }


    return render(
        request,
        'dashboard/customer_orders.html',
        context
    )
## =========================================================
# CANCEL ORDER ITEM
# =========================================================

def cancel_order_item(request, item_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # ONLY POST REQUEST
    # -----------------------------------------------------

    if request.method != 'POST':
        return redirect('customer_orders')


    # -----------------------------------------------------
    # GET ORDER ITEM
    # -----------------------------------------------------

    try:

        order_item = OrderItem.objects.select_related(
            'order',
            'product'
        ).get(
            id=item_id,
            order__customer_id=customer_id
        )

    except OrderItem.DoesNotExist:

        messages.error(
            request,
            'Order item not found.'
        )

        return redirect('customer_orders')


    # -----------------------------------------------------
    # CHECK CANCELLATION STATUS
    # -----------------------------------------------------

    if order_item.item_status not in [
        'PENDING',
        'PROCESSING'
    ]:

        messages.error(
            request,
            'This product can no longer be cancelled.'
        )

        return redirect('customer_orders')


    # -----------------------------------------------------
    # CANCEL PRODUCT
    # -----------------------------------------------------

    try:

        with transaction.atomic():

            # =================================================
            # LOCK PRODUCT
            # =================================================

            product = Product.objects.select_for_update().get(
                id=order_item.product_id
            )


            # =================================================
            # RESTORE STOCK
            # =================================================

            product.stock_quantity = (
                product.stock_quantity
                + order_item.quantity
            )

            product.save(
                update_fields=[
                    'stock_quantity'
                ]
            )


            # =================================================
            # CHANGE ITEM STATUS TO CANCELLED
            # =================================================

            order_item.item_status = 'CANCELLED'

            order_item.save(
                update_fields=[
                    'item_status'
                ]
            )


            # =================================================
            # GET ORDER
            # =================================================

            order = order_item.order


            # =================================================
            # GET REMAINING ACTIVE ITEMS
            # =================================================

            active_items = OrderItem.objects.filter(
                order=order
            ).exclude(
                item_status='CANCELLED'
            )


            # =================================================
            # CALCULATE REMAINING ORDER TOTAL
            # =================================================

            new_total = 0

            for item in active_items:

                new_total += (
                    item.price * item.quantity
                )


            # =================================================
            # CHECK WHETHER ANY ACTIVE ITEM REMAINS
            # =================================================

            active_items_exist = active_items.exists()


            # =================================================
            # IF ALL PRODUCTS ARE CANCELLED
            # =================================================

            if not active_items_exist:

                # ---------------------------------------------
                # ORDER TOTAL
                # ---------------------------------------------

                order.total_amount = 0


                # ---------------------------------------------
                # ORDER STATUS
                # ---------------------------------------------

                order.order_status = 'CANCELLED'


                order.save(
                    update_fields=[
                        'total_amount',
                        'order_status'
                    ]
                )


                # ---------------------------------------------
                # PAYMENT
                # ---------------------------------------------

                try:

                    payment = order.payment

                    payment.amount = 0

                    payment.payment_status = 'CANCELLED'

                    payment.save(
                        update_fields=[
                            'amount',
                            'payment_status'
                        ]
                    )

                except Payment.DoesNotExist:

                    pass


            # =================================================
            # IF SOME PRODUCTS ARE STILL ACTIVE
            # =================================================

            else:

                # ---------------------------------------------
                # UPDATE ORDER TOTAL
                # ---------------------------------------------

                order.total_amount = new_total


                # ---------------------------------------------
                # DETERMINE ORDER STATUS
                #
                # Order status is based on remaining products.
                # ---------------------------------------------

                remaining_statuses = list(
                    active_items.values_list(
                        'item_status',
                        flat=True
                    )
                )


                if 'SHIPPED' in remaining_statuses:

                    order.order_status = 'SHIPPED'

                elif 'PROCESSING' in remaining_statuses:

                    order.order_status = 'PROCESSING'

                elif 'PENDING' in remaining_statuses:

                    order.order_status = 'PENDING'

                elif 'DELIVERED' in remaining_statuses:

                    order.order_status = 'DELIVERED'


                order.save(
                    update_fields=[
                        'total_amount',
                        'order_status'
                    ]
                )


                # ---------------------------------------------
                # UPDATE PAYMENT AMOUNT
                # ---------------------------------------------

                try:

                    payment = order.payment

                    # Only change amount for unpaid/pending payment

                    if payment.payment_status == 'PENDING':

                        payment.amount = new_total

                        payment.save(
                            update_fields=[
                                'amount'
                            ]
                        )

                except Payment.DoesNotExist:

                    pass


        # =====================================================
        # SUCCESS MESSAGE
        # =====================================================

        messages.success(
            request,
            f'{order_item.product.product_name} '
            f'cancelled successfully.'
        )


    except Exception as error:

        print(
            '========================================'
        )
        print('CANCEL ORDER ERROR:',
              repr(error)
        )
        print(
            '==================================='
        )

        # =====================================================
        # ERROR
        # =====================================================

        messages.error(
            request,
            f'Cancellation error: {error}'
        )

        


    return redirect('customer_orders')

# =========================================================
# CUSTOMER CART
# =========================================================

def customer_cart(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER CAN ACCESS CART
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET CUSTOMER CART
    # -----------------------------------------------------

    try:

        cart = Cart.objects.get(
            customer=customer
        )

    except Cart.DoesNotExist:

        cart = None


    # -----------------------------------------------------
    # GET CART ITEMS
    # -----------------------------------------------------

    cart_items = []

    total = 0


    if cart:

        cart_items = list(
            CartItem.objects.filter(
                cart=cart
            ).select_related(
                'product',
                'product__category'
            )
        )
        

        # -------------------------------------------------
        # CALCULATE SUBTOTAL
        # -------------------------------------------------

        for item in cart_items:

            item.subtotal = (
                item.product.price * item.quantity
            )

            total += item.subtotal


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        'customer': customer,

        'cart': cart,

        'cart_items': cart_items,

        'total': total,

    }


    return render(

        request,

        'dashboard/customer_cart.html',

        context

    )
# =========================================================
# CHECKOUT
# =========================================================

def checkout(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')


    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET CART
    # -----------------------------------------------------

    try:

        cart = Cart.objects.get(
            customer=customer
        )

    except Cart.DoesNotExist:

        messages.warning(
            request,
            'Your cart is empty.'
        )

        return redirect('customer_cart')


    # -----------------------------------------------------
    # GET CART ITEMS
    # -----------------------------------------------------

    cart_items = list(
        CartItem.objects.filter(
            cart=cart
        ).select_related(
            'product',
            'product__category'
        )
    )


    # -----------------------------------------------------
    # EMPTY CART CHECK
    # -----------------------------------------------------

    if not cart_items:

        messages.warning(
            request,
            'Your cart is empty.'
        )

        return redirect('customer_cart')


    # -----------------------------------------------------
    # CALCULATE TOTAL
    # -----------------------------------------------------

    total = 0


    for item in cart_items:

        item.subtotal = (
            item.product.price * item.quantity
        )

        total += item.subtotal


    # -----------------------------------------------------
    # CHECK STOCK BEFORE CHECKOUT
    # -----------------------------------------------------

    for item in cart_items:

        if item.quantity > item.product.stock_quantity:

            messages.error(
                request,
                f'Only {item.product.stock_quantity} '
                f'item(s) of {item.product.product_name} '
                f'are available.'
            )

            return redirect('customer_cart')


    # -----------------------------------------------------
    # CHECK SHIPPING ADDRESS
    # -----------------------------------------------------

    if not customer.address:

        messages.warning(
            request,
            'Please add your shipping address before checkout.'
        )

        return redirect(
            'customer_profile'
        )


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        'customer': customer,

        'cart': cart,

        'cart_items': cart_items,

        'total': total,

    }


    return render(

        request,

        'dashboard/checkout.html',

        context

    )
# =========================================================
# PLACE ORDER - CASH ON DELIVERY
# =========================================================

# =========================================================
# PLACE ORDER - CASH ON DELIVERY
# =========================================================

def place_order(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    # -----------------------------------------------------
    # ONLY POST REQUEST
    # -----------------------------------------------------

    if request.method != 'POST':

        return redirect('checkout')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')


    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # CHECK SHIPPING ADDRESS
    # -----------------------------------------------------

    if not customer.address:

        messages.error(
            request,
            'Please add your shipping address before placing the order.'
        )

        return redirect('customer_profile')


    # -----------------------------------------------------
    # GET CUSTOMER CART
    # -----------------------------------------------------

    try:

        cart = Cart.objects.get(
            customer=customer
        )

    except Cart.DoesNotExist:

        messages.error(
            request,
            'Your cart is empty.'
        )

        return redirect('customer_cart')


    # -----------------------------------------------------
    # GET CART ITEMS
    # -----------------------------------------------------

    cart_items = list(
        CartItem.objects.filter(
            cart=cart
        ).select_related(
            'product'
        )
    )


    if not cart_items:

        messages.error(
            request,
            'Your cart is empty.'
        )

        return redirect('customer_cart')


    # -----------------------------------------------------
    # CREATE ORDER
    # -----------------------------------------------------

    try:

        with transaction.atomic():

            total = 0

            locked_items = []


            # ---------------------------------------------
            # CHECK STOCK
            # ---------------------------------------------

            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )


                if product.stock_quantity < item.quantity:

                    raise ValueError(
                        f'Only {product.stock_quantity} '
                        f'item(s) of {product.product_name} '
                        f'are available.'
                    )


                # -----------------------------------------
                # CALCULATE ITEM TOTAL
                # -----------------------------------------

                item_total = (
                    product.price * item.quantity
                )

                total += item_total


                locked_items.append(
                    (item, product)
                )


            # ---------------------------------------------
            # CREATE ORDER
            # ---------------------------------------------

            order = Order.objects.create(

                customer=customer,

                total_amount=total,

                order_status='PENDING',

                shipping_address=customer.address,

                created_at=timezone.now()

            )


            # ---------------------------------------------
            # CREATE ORDER ITEMS
            # ---------------------------------------------

            for item, product in locked_items:

                OrderItem.objects.create(

                    order=order,

                    product=product,

                    vendor=product.vendor,

                    quantity=item.quantity,

                    price=product.price,
                    item_status='PENDING'

                )
                Notification.objects.create(
                    vendor=product.vendor,
                    order=order,
                    message=f'New order #{order.id} recieved for {product.product_name}',
                    is_read=False,
                    created_at=timezone.now()

                )

                # -----------------------------------------
                # REDUCE PRODUCT STOCK
                # -----------------------------------------

                product.stock_quantity -= item.quantity

                product.save(
                    update_fields=[
                        'stock_quantity'
                    ]
                )


            # ---------------------------------------------
            # CREATE COD PAYMENT
            # ---------------------------------------------

            Payment.objects.create(

                order=order,

                payment_method='COD',

                payment_status='PENDING',

                amount=total,

                transaction_id=None,

                paid_at=None

            )


            # ---------------------------------------------
            # CLEAR CART
            # ---------------------------------------------

            CartItem.objects.filter(
                cart=cart
            ).delete()


        # -------------------------------------------------
        # ORDER SUCCESS
        # -------------------------------------------------

                # =================================================
        # ORDER SUCCESS
        # =================================================

        return render(
            request,
            'dashboard/order_success.html',
            {
                'order': order
            }
        )


    except ValueError as error:

        messages.error(
            request,
            str(error)
        )

        return redirect(
            'customer_cart'
        )


    except Exception as error:

        messages.error(
            request,
            'Unable to place the order. Please try again.'
        )

        print(
            'PLACE ORDER ERROR:',
            error
        )

        return redirect(
            'customer_cart'
        )
# =========================================================
# ADD TO CART
# =========================================================

def add_to_cart(request, product_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER CAN ADD TO CART
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    customer_id = request.session.get('user_id')

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET PRODUCT
    # -----------------------------------------------------

    product = get_object_or_404(
        Product,
        id=product_id
    )


    # -----------------------------------------------------
    # CHECK STOCK
    # -----------------------------------------------------

    if product.stock_quantity <= 0:

        messages.error(
            request,
            'Sorry, this product is out of stock.'
        )

        return redirect('customer_dashboard')


    # -----------------------------------------------------
    # GET OR CREATE CUSTOMER CART
    # -----------------------------------------------------

    cart, created = Cart.objects.get_or_create(
        customer=customer,
        defaults={
            'created_at': timezone.now()
        }
    )


    # -----------------------------------------------------
    # GET OR CREATE CART ITEM
    # -----------------------------------------------------

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            'quantity': 1
        }
    )


    # -----------------------------------------------------
    # IF PRODUCT ALREADY EXISTS
    # -----------------------------------------------------

    if not created:

        if cart_item.quantity < product.stock_quantity:

            cart_item.quantity += 1

            cart_item.save(
                update_fields=['quantity']
            )

        else:

            messages.warning(
                request,
                'You have reached the available stock for this product.'
            )

            return redirect('customer_dashboard')


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    messages.success(
        request,
        f'{product.product_name} added to cart successfully.'
    )


    return redirect('customer_dashboard')
# =========================================================
# INCREASE CART ITEM QUANTITY
# =========================================================

def increase_cart_quantity(request, item_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET CART
    # -----------------------------------------------------

    cart = get_object_or_404(
        Cart,
        customer=customer
    )


    # -----------------------------------------------------
    # GET CART ITEM
    # -----------------------------------------------------

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart
    )


    # -----------------------------------------------------
    # CHECK STOCK
    # -----------------------------------------------------

    if cart_item.quantity < cart_item.product.stock_quantity:

        cart_item.quantity += 1

        cart_item.save(
            update_fields=['quantity']
        )

    else:

        messages.warning(
            request,
            'You have reached the available stock for this product.'
        )


    return redirect('customer_cart')


# =========================================================
# DECREASE CART ITEM QUANTITY
# =========================================================

def decrease_cart_quantity(request, item_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET CART
    # -----------------------------------------------------

    cart = get_object_or_404(
        Cart,
        customer=customer
    )


    # -----------------------------------------------------
    # GET CART ITEM
    # -----------------------------------------------------

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart
    )


    # -----------------------------------------------------
    # DECREASE QUANTITY
    # -----------------------------------------------------

    if cart_item.quantity > 1:

        cart_item.quantity -= 1

        cart_item.save(
            update_fields=['quantity']
        )

    else:

        pass


    return redirect('customer_cart')
# =========================================================
# REMOVE CART ITEM
# =========================================================

def remove_cart_item(request, item_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')

    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':
        return redirect('login')

    customer_id = request.session.get('user_id')

    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')

    # -----------------------------------------------------
    # GET CUSTOMER CART
    # -----------------------------------------------------

    cart = get_object_or_404(
        Cart,
        customer=customer
    )

    # -----------------------------------------------------
    # GET CART ITEM
    # IMPORTANT: cart=cart prevents removing
    # another customer's cart item
    # -----------------------------------------------------

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart
    )

    # -----------------------------------------------------
    # DELETE CART ITEM
    # -----------------------------------------------------

    cart_item.delete()

    # -----------------------------------------------------
    # REDIRECT TO CART
    # -----------------------------------------------------

    return redirect('customer_cart')

# # =========================================================
# CUSTOMER WISHLIST
# =========================================================

def customer_wishlist(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET CUSTOMER
    # -----------------------------------------------------

    try:

        customer = User.objects.get(
            id=customer_id,
            role='CUSTOMER'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET WISHLIST
    # -----------------------------------------------------

    wishlist_items = Wishlist.objects.filter(
        customer_id=customer_id
    ).select_related(
        'product',
        'product__category'
    ).order_by(
        '-created_at'
    )


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        'customer': customer,

        'wishlist_items': wishlist_items,

    }


    return render(

        request,

        'dashboard/customer_wishlist.html',

        context

    )
# =========================================================
# ADD TO WISHLIST
# =========================================================

def add_to_wishlist(request, product_id):

    print("======================================")
    print("ADD TO WISHLIST CALLED")
    print("METHOD:", request.method)
    print("PRODUCT ID:", product_id)
    print("USER ID:", request.session.get('user_id'))
    print("USER ROLE:", request.session.get('user_role'))
    print("======================================")


    # CHECK LOGIN
    if not request.session.get('user_id'):
        print("ERROR: USER NOT LOGGED IN")
        return redirect('login')


    # CHECK CUSTOMER
    if request.session.get('user_role') != 'CUSTOMER':
        print("ERROR: USER IS NOT CUSTOMER")
        return redirect('login')


    # ONLY POST
    if request.method != 'POST':
        print("ERROR: REQUEST IS NOT POST")
        return redirect('customer_dashboard')


    customer_id = request.session.get('user_id')


    # GET CUSTOMER
    customer = get_object_or_404(
        User,
        id=customer_id,
        role='CUSTOMER'
    )


    print("CUSTOMER:", customer.id, customer.name)


    # GET PRODUCT
    product = get_object_or_404(
        Product,
        id=product_id
    )


    print("PRODUCT:", product.id, product.product_name)


    # CREATE WISHLIST
    wishlist_item, created = Wishlist.objects.get_or_create(
        customer=customer,
        product=product
    )


    print("WISHLIST ID:", wishlist_item.id)
    print("CREATED:", created)


    if created:

        messages.success(
            request,
            f'{product.product_name} added to wishlist.'
        )

    else:

        messages.info(
            request,
            f'{product.product_name} is already in your wishlist.'
        )


    return redirect('customer_dashboard')
# =========================================================
# REMOVE FROM WISHLIST
# =========================================================

def remove_from_wishlist(request, product_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    # -----------------------------------------------------
    # ONLY POST
    # -----------------------------------------------------

    if request.method != 'POST':

        return redirect('customer_wishlist')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # DELETE ONLY THIS CUSTOMER'S WISHLIST ITEM
    # -----------------------------------------------------

    wishlist_item = Wishlist.objects.filter(

        customer_id=customer_id,

        product_id=product_id

    ).first()


    if wishlist_item:

        wishlist_item.delete()

        messages.success(

            request,

            'Product removed from wishlist.'

        )


    return redirect('customer_wishlist')

 # =========================================================
# ADD PRODUCT REVIEW
# =========================================================

def add_review(request, product_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY CUSTOMER
    # -----------------------------------------------------

    if request.session.get('user_role') != 'CUSTOMER':

        return redirect('login')


    customer_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET PRODUCT
    # -----------------------------------------------------

    product = get_object_or_404(
        Product,
        id=product_id
    )


    # -----------------------------------------------------
    # CHECK DELIVERED ORDER
    # -----------------------------------------------------

    delivered_item = OrderItem.objects.filter(
    product_id=product_id,
    order__customer_id=customer_id,
    item_status__iexact='DELIVERED'
    ).first()

    if not delivered_item:

        messages.error(
            request,
            'You can review this product only after it has been delivered.'
        )

        return redirect('customer_orders')


    # -----------------------------------------------------
    # CHECK DUPLICATE REVIEW
    # -----------------------------------------------------

    existing_review = Review.objects.filter(

        customer_id=customer_id,

        product_id=product_id

    ).first()


    if existing_review:

        messages.info(
            request,
            'You have already reviewed this product.'
        )

        return redirect('customer_orders')


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == 'POST':

        rating = request.POST.get('rating')

        comment = request.POST.get('comment', '').strip()


        # -------------------------------------------------
        # VALIDATE RATING
        # -------------------------------------------------

        try:

            rating = int(rating)

        except (TypeError, ValueError):

            messages.error(
                request,
                'Please select a valid rating.'
            )

            return redirect(
                'add_review',
                product_id=product_id
            )


        if rating < 1 or rating > 5:

            messages.error(
                request,
                'Rating must be between 1 and 5 stars.'
            )

            return redirect(
                'add_review',
                product_id=product_id
            )


        # -------------------------------------------------
        # SAVE REVIEW
        # -------------------------------------------------

        Review.objects.create(

            customer_id=customer_id,

            product_id=product_id,

            rating=rating,

            comment=comment,

            created_at=timezone.now()

        )


        messages.success(
            request,
            'Your review has been submitted successfully!'
        )


        return redirect(
            'customer_orders'
        )


    # -----------------------------------------------------
    # SHOW REVIEW PAGE
    # -----------------------------------------------------

    return render(
        request,
        'dashboard/add_review.html',
        {
            'product': product
        }
    )   
# =========================================================
# VENDOR DASHBOARD
# =========================================================

def vendor_dashboard(request):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get logged-in vendor
    # -----------------------------------------------------

    try:

        vendor = User.objects.get(
            id=vendor_id,
            role='VENDOR'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # ONLY THIS VENDOR'S PRODUCTS
    # -----------------------------------------------------

    products = Product.objects.filter(
        vendor_id=vendor.id
    ).select_related(
        'category'
    ).order_by(
        '-id'
    )


    # -----------------------------------------------------
    # ONLY ORDERS CONTAINING THIS VENDOR'S PRODUCTS
    # -----------------------------------------------------

    order_items = OrderItem.objects.filter(
        vendor_id=vendor.id
    ).select_related(
        'order',
        'order__customer',
        'product'
    ).order_by(
        '-order__created_at'
    )


    # -----------------------------------------------------
    # Dashboard counts
    # -----------------------------------------------------

    product_count = products.count()

    order_count = order_items.values(
        'order_id'
    ).distinct().count()

    # -----------------------------------------------------
    # NEW / UNVIEWED ORDERS
    # -----------------------------------------------------

    new_order_count = OrderItem.objects.filter(

        vendor_id=vendor.id,
        is_viewed=False

    ).count()

    # -----------------------------------------------------
    # UNREAD NOTIFICATIONS
    # -----------------------------------------------------

    notification_count = Notification.objects.filter(

        vendor_id=vendor.id,
        is_read=False

    ).count()



    # -----------------------------------------------------
    # Context
    # -----------------------------------------------------

    context = {

        'vendor': vendor,

        'products': products,

        'product_count': product_count,

        'order_items': order_items,

        'order_count': order_count,

       'new_order_count': new_order_count,

        'notification_count': notification_count,


    }


    return render(
        request,
        'dashboard/vendor_dashboard.html',
        context
    )


# =========================================================
# VIEW PRODUCT
# =========================================================

def view_product(request, product_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get only this vendor's product
    # -----------------------------------------------------

    try:

        product = Product.objects.select_related(
            'category'
        ).get(
            id=product_id,
            vendor_id=vendor_id
        )

    except Product.DoesNotExist:

        return redirect('vendor_dashboard')


    return render(
        request,
        'dashboard/view_product.html',
        {
            'product': product
        }
    )


# =========================================================
# ADD PRODUCT
# =========================================================

def add_product(request):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')
    

    # -----------------------------------------------------
    # Get logged-in vendor
    # -----------------------------------------------------

    try:

        vendor = User.objects.get(
            id=vendor_id,
            role='VENDOR'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # Categories
    # -----------------------------------------------------

    categories = Category.objects.all().order_by(
        'category_name'
    )


    # -----------------------------------------------------
    # SAVE PRODUCT
    # -----------------------------------------------------

    if request.method == 'POST':

        product_name = request.POST.get(
            'product_name',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        category_id = request.POST.get(
            'category'
        )

        price = request.POST.get(
            'price'
        )

        stock_quantity = request.POST.get(
            'stock_quantity'
        )

        product_image = request.FILES.get(
            'product_image'
        )


        # -------------------------------------------------
        # Basic validation
        # -------------------------------------------------

        if not product_name:

            messages.error(
                request,
                'Product name is required.'
            )

            return render(
                request,
                'dashboard/add_product.html',
                {
                    'vendor': vendor,
                    'categories': categories
                }
            )


        if not category_id:

            messages.error(
                request,
                'Please select a category.'
            )

            return render(
                request,
                'dashboard/add_product.html',
                {
                    'vendor': vendor,
                    'categories': categories
                }
            )


        if not price:

            messages.error(
                request,
                'Price is required.'
            )

            return render(
                request,
                'dashboard/add_product.html',
                {
                    'vendor': vendor,
                    'categories': categories
                }
            )


        if not stock_quantity:

            stock_quantity = 0


        # -------------------------------------------------
        # IMAGE UPLOAD
        # -------------------------------------------------

        image_path = None


        if product_image:

            # Create media/products folder

            upload_directory = os.path.join(
                settings.MEDIA_ROOT,
                'products'
            )

            os.makedirs(
                upload_directory,
                exist_ok=True
            )


            # Image filename

            image_name = product_image.name


            # Full image path

            image_file_path = os.path.join(
                upload_directory,
                image_name
            )


            # Save image

            with open(
                image_file_path,
                'wb+'
            ) as destination:

                for chunk in product_image.chunks():

                    destination.write(chunk)


            # Save path in database

            image_path = (
                'products/' + image_name
            )


        # -------------------------------------------------
        # Create Product
        # -------------------------------------------------

        Product.objects.create(

            vendor=vendor,

            category_id=category_id,

            product_name=product_name,

            description=description,

            price=price,

            stock_quantity=stock_quantity,

            product_image=image_path,

            created_at=timezone.now()

        )


        # -------------------------------------------------
        # Success message
        # -------------------------------------------------

        messages.success(
            request,
            'Product added successfully.'
        )


        return redirect(
            'vendor_dashboard'
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render(
        request,
        'dashboard/add_product.html',
        {
            'vendor': vendor,
            'categories': categories
        }
    )


# =========================================================
# EDIT / UPDATE PRODUCT
# =========================================================

def edit_product(request, product_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get only this vendor's product
    # -----------------------------------------------------

    product = get_object_or_404(
        Product,
        id=product_id,
        vendor_id=vendor_id
    )


    # -----------------------------------------------------
    # Categories
    # -----------------------------------------------------

    categories = Category.objects.all().order_by(
        'category_name'
    )


    # -----------------------------------------------------
    # UPDATE PRODUCT
    # -----------------------------------------------------

    if request.method == 'POST':

        product.product_name = request.POST.get(
            'product_name'
        )

        product.description = request.POST.get(
            'description'
        )

        product.price = request.POST.get(
            'price'
        )

        product.stock_quantity = request.POST.get(
            'stock_quantity'
        )


        # -------------------------------------------------
        # UPDATE CATEGORY
        # -------------------------------------------------

        category_id = request.POST.get(
            'category'
        )


        if category_id:

            product.category_id = category_id


        # -------------------------------------------------
        # UPDATE PRODUCT IMAGE
        # -------------------------------------------------

        product_image = request.FILES.get(
            'product_image'
        )


        if product_image:

            # Create media/products folder

            upload_directory = os.path.join(
                settings.MEDIA_ROOT,
                'products'
            )

            os.makedirs(
                upload_directory,
                exist_ok=True
            )


            # Image filename

            image_name = product_image.name


            # Full image path

            image_file_path = os.path.join(
                upload_directory,
                image_name
            )


            # Save uploaded image

            with open(
                image_file_path,
                'wb+'
            ) as destination:

                for chunk in product_image.chunks():

                    destination.write(chunk)


            # Save image path in database

            product.product_image = (
                'products/' + image_name
            )


        # -------------------------------------------------
        # Save Product
        # -------------------------------------------------

        product.save()


        messages.success(
            request,
            'Product updated successfully!'
        )


        return redirect(
            'vendor_dashboard'
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render(
        request,
        'dashboard/edit_product.html',
        {
            'product': product,
            'categories': categories
        }
    )


## =========================================================
# DELETE PRODUCT
# =========================================================

def delete_product(request, product_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get only this vendor's product
    # -----------------------------------------------------

    product = get_object_or_404(
        Product,
        id=product_id,
        vendor_id=vendor_id
    )


    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    if request.method == 'POST':

        # -------------------------------------------------
        # Check whether this product is already ordered
        # -------------------------------------------------

        if OrderItem.objects.filter(
            product_id=product.id
        ).exists():

            messages.error(
                request,
                'This product cannot be deleted because it is already associated with an order.'
            )

            return redirect(
                'vendor_dashboard'
            )


        # -------------------------------------------------
        # Product has never been ordered
        # -------------------------------------------------

        product.delete()

        messages.success(
            request,
            'Product deleted successfully!'
        )

        return redirect(
            'vendor_dashboard'
        )


    # -----------------------------------------------------
    # Confirmation page
    # -----------------------------------------------------

    return render(
        request,
        'dashboard/delete_product.html',
        {
            'product': product
        }
    )

# =========================================================
# VENDOR ORDERS
# =========================================================

# =========================================================
# VENDOR ORDERS
# =========================================================

def vendor_orders(request):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':
        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get logged-in vendor
    # -----------------------------------------------------

    try:

        vendor = User.objects.get(
            id=vendor_id,
            role='VENDOR'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # =====================================================
    # CONFIRM ORDER ITEM
    # =====================================================

    if request.method == 'POST':

        item_id = request.POST.get('item_id')

        if item_id:

            try:

                order_item = OrderItem.objects.select_related(
                    'order',
                    'order__customer',
                    'product'
                ).get(
                    id=item_id,
                    vendor_id=vendor.id
                )


                # -----------------------------------------
                # Only PENDING items can be confirmed
                # -----------------------------------------

                                # -----------------------------------------
                # Only PENDING items can be confirmed
                # -----------------------------------------

                if order_item.item_status == 'PENDING':

                    # -------------------------------------
                    # CONFIRM ORDER ITEM
                    # -------------------------------------

                    order_item.item_status = 'CONFIRMED'

                    order_item.save(
                        update_fields=['item_status']
                    )


                    # =====================================
                    # SEND HTML CONFIRMATION EMAIL
                    # =====================================

                    customer = order_item.order.customer
                    product = order_item.product
                    order = order_item.order

                    product_image = ""

                    if product.product_image:
                        product_image = request.build_absolute_uri(
                            settings.MEDIA_URL + str(product.product_image)
                        )

                    view_order_url = request.build_absolute_uri(
                        reverse('customer_orders')
                    )

                    html_message = render_to_string(
                        'dashboard/order_email.html',
                        {
                            'customer_name': customer.name,
                            'status_title': 'Order Confirmed',
                            'status_message': (
                                f'Your order #{order.id} '
                                f'has been confirmed by the vendor.'
                            ),
                            'product_name': product.product_name,
                            'product_image': product_image,
                            'quantity': order_item.quantity,
                            'price': order_item.price,
                            'order_id': order.id,
                            'total_amount': order.total_amount,
                            'payment_method': (
                                order.payment.payment_method
                                if hasattr(order, 'payment')
                                and order.payment
                                else 'Cash on delivery'
                            ),
                            'shipping_address': order.shipping_address,
                            'view_order_url': view_order_url,
                        }
                    )

                    
                    try:

                        email = EmailMultiAlternatives(
                            subject='Order Confirmed - happiShoppi',
                            body=(
                                f'Your order #{order.id} '
                                f'has been confirmed.'
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[customer.email]
                        )

                        email.attach_alternative(
                            html_message,
                            'text/html'
                        )


                        # -------------------------------------
                        # EMBED PRODUCT IMAGE IN EMAIL
                        # -------------------------------------

                        if product.product_image:

                            image_path = os.path.join(
                                settings.MEDIA_ROOT,
                                str(product.product_image)
                            )

                            if os.path.exists(image_path):

                                with open(
                                    image_path,
                                    'rb'
                                ) as image_file:

                                    image = MIMEImage(
                                        image_file.read(),
                                        _subtype=os.path.splitext(image_path)[1].replace('.', '').lower()
                                    )

                                    image.add_header(
                                        'Content-ID',
                                        '<product_image>'
                                    )

                                    image.add_header(
                                        'Content-Disposition',
                                        'inline',
                                        filename=os.path.basename(
                                            image_path
                                        )
                                    )

                                    email.attach(
                                        image
                                    )
                        email.send()
                        messages.success(
                            request,
                            f'Order confirmed and email sent '
                            f'to {customer.email}.'
                        )    
                    except Exception as e:

                        print(
                            'CONFIRMATION EMAIL ERROR:',
                            e
                        )

                        messages.warning(
                            request,
                            'Order confirmed, but confirmation email '
                            'could not be sent.'
                        )

                else:

                    messages.warning(
                        request,
                        'This order has already been confirmed or processed.'
                    )
            except OrderItem.DoesNotExist:

                messages.error(

                    request,

                    'Order item not found.'

                )


        return redirect('vendor_orders')


    # -----------------------------------------------------
    # Get ONLY this vendor's order items
    # -----------------------------------------------------

    order_items = OrderItem.objects.filter(

        vendor_id=vendor.id

    ).select_related(

        'order',
        'order__customer',
        'product'

    ).order_by(

        '-order__created_at'

    )

     # -----------------------------------------------------
    # MARK ALL NEW ORDERS AS VIEWED
    # -----------------------------------------------------
    #
    # When vendor opens Orders:
    #
    # 3 new orders -> 3
    #
    # After opening this page:
    #
    # 3 -> 0
    #
    # -----------------------------------------------------

    OrderItem.objects.filter(

        vendor_id=vendor.id,

        is_viewed=False

    ).update(

        is_viewed=True

    )

    # -----------------------------------------------------
    # CURRENT NOTIFICATION COUNT
    # -----------------------------------------------------

    notification_count = Notification.objects.filter(

        vendor_id=vendor.id,

        is_read=False

    ).count()





    # -----------------------------------------------------
    # Context
    # -----------------------------------------------------

    context = {

        'vendor': vendor,

        'order_items': order_items,
        'notification_count': notification_count,

        'new_order_count': 0,


    }


    # -----------------------------------------------------
    # Render Vendor Orders page
    # -----------------------------------------------------

    return render(

        request,

        'dashboard/vendor_orders.html',

        context

    )
# UPDATE VENDOR ORDER ITEM STATUS
# =========================================================

# =========================================================
# UPDATE VENDOR ORDER ITEM STATUS
# =========================================================

def update_vendor_order_status(request, item_id):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY VENDOR CAN ACCESS
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':
        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # ONLY POST REQUEST ALLOWED
    # -----------------------------------------------------

    if request.method != 'POST':
        return redirect('vendor_orders')


    # -----------------------------------------------------
    # GET THIS VENDOR'S ORDER ITEM
    # -----------------------------------------------------

    item = get_object_or_404(
        OrderItem,
        id=item_id,
        vendor_id=vendor_id
    )


    # -----------------------------------------------------
    # GET NEW STATUS
    # -----------------------------------------------------

    new_status = request.POST.get('status')


    # -----------------------------------------------------
    # ALLOWED STATUS TRANSITIONS
    # -----------------------------------------------------

    allowed_transitions = {

        'CONFIRMED': 'PROCESSING',

        'PROCESSING': 'SHIPPED',

        'SHIPPED': 'DELIVERED',

    }


    current_status = item.item_status


    # -----------------------------------------------------
    # CANNOT UPDATE CANCELLED PRODUCT
    # -----------------------------------------------------

    if current_status == 'CANCELLED':

        messages.error(
            request,
            'This product was cancelled by the customer and cannot be updated.'
        )

        return redirect('vendor_orders')


    # -----------------------------------------------------
    # CHECK VALID CURRENT STATUS
    # -----------------------------------------------------

    if current_status not in allowed_transitions:

        messages.error(
            request,
            'This order cannot be updated from its current status.'
        )

        return redirect('vendor_orders')


    expected_status = allowed_transitions[current_status]


    # -----------------------------------------------------
    # CHECK REQUESTED STATUS
    # -----------------------------------------------------

    if new_status != expected_status:

        messages.error(
            request,
            'Invalid order status update.'
        )

        return redirect('vendor_orders')


    # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

    item.item_status = new_status

    item.save(
        update_fields=[
            'item_status'
        ]
    )


    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer = item.order.customer

    customer_name = customer.name

    customer_email = customer.email

    product_name = item.product.product_name

    quantity = item.quantity

    price = item.price

    order_id = item.order.id

    total_amount = item.order.total_amount

    shipping_address = item.order.shipping_address


    # =====================================================
    # CONFIRMED EMAIL
    # =====================================================

    if new_status == 'CONFIRMED':

        subject = 'Order Confirmed - happiShoppi'


        message = f"""
Dear {customer_name},

Your order has been successfully confirmed by the vendor.

Order Number: #{order_id}

Product: {product_name}
Quantity: {quantity}
Price: ₹{price}

Total Amount: ₹{total_amount}

Your order is now being prepared by the vendor.

You can track your order status from the "My Orders"
section of your happiShoppi account.

Thank you for shopping with happiShoppi.

happiShoppi Team
"""


        try:

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [customer_email],
                fail_silently=False
            )


            messages.success(
                request,
                f'Product confirmed and confirmation email sent to {customer_email}.'
            )


        except Exception as e:

            messages.warning(
                request,
                f'Product confirmed, but confirmation email could not be sent: {str(e)}'
            )


    # =====================================================
    # DELIVERED EMAIL
    # =====================================================

    elif new_status == 'DELIVERED':

        subject = 'Order Delivered - happiShoppi'


        message = f"""
Dear {customer_name},

Your order has been successfully delivered.

Order Number: #{order_id}

Product: {product_name}
Quantity: {quantity}
Price: ₹{price}

Total Amount: ₹{total_amount}

Delivery Address:
{shipping_address}

We hope you enjoy your purchase.

Thank you for shopping with happiShoppi.

happiShoppi Team
"""


        try:

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [customer_email],
                fail_silently=False
            )


            messages.success(
                request,
                f'Product delivered and delivery email sent to {customer_email}.'
            )


        except Exception as e:

            messages.warning(
                request,
                f'Product delivered, but delivery email could not be sent: {str(e)}'
            )


    # =====================================================
    # PROCESSING / SHIPPED
    # NO EMAIL
    # =====================================================

    else:

        messages.success(
            request,
            f'Product status updated to {new_status.title()}.'
        )


    # -----------------------------------------------------
    # RETURN TO VENDOR ORDERS
    # -----------------------------------------------------

    return redirect('vendor_orders')
    
# =========================================================
# VENDOR NOTIFICATIONS
# =========================================================
# =========================================================
# VENDOR NOTIFICATIONS
# =========================================================

def vendor_notifications(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY VENDOR
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # GET LOGGED-IN VENDOR
    # -----------------------------------------------------

    try:

        vendor = User.objects.get(
            id=vendor_id,
            role='VENDOR'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # -----------------------------------------------------
    # GET THIS VENDOR'S NOTIFICATIONS
    # -----------------------------------------------------

    notifications = Notification.objects.filter(

        vendor_id=vendor.id

    ).select_related(

        'order',
        'order__customer'

    ).order_by(

        '-created_at'

    )


    # -----------------------------------------------------
    # COUNT UNREAD NOTIFICATIONS
    # -----------------------------------------------------

    notification_count = notifications.filter(

        is_read=False

    ).count()


    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {

        'vendor': vendor,

        'notifications': notifications,

        'notification_count': notification_count,

    }


    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(

        request,

        'dashboard/vendor_notifications.html',

        context

    )

# =========================================================
# OPEN VENDOR NOTIFICATION
# =========================================================

def open_vendor_notification(request, notification_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # Only Vendor can access
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # Get ONLY this vendor's notification
    # -----------------------------------------------------

    notification = get_object_or_404(

        Notification,

        id=notification_id,

        vendor_id=vendor_id

    )


    # -----------------------------------------------------
    # Mark notification as READ
    # -----------------------------------------------------

    if not notification.is_read:

        notification.is_read = True

        notification.save(

            update_fields=['is_read']

        )


    # -----------------------------------------------------
    # Open vendor orders page
    # -----------------------------------------------------

    return redirect('vendor_orders')

# =========================================================
# CLEAR ALL NOTIFICATIONS
# =========================================================

def clear_vendor_notifications(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):

        return redirect('login')


    # -----------------------------------------------------
    # ONLY VENDOR
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':

        return redirect('login')


    vendor_id = request.session.get('user_id')


    # -----------------------------------------------------
    # ONLY POST
    # -----------------------------------------------------

    if request.method != 'POST':

        return redirect(

            'vendor_notifications'

        )


    # -----------------------------------------------------
    # DELETE THIS VENDOR'S NOTIFICATIONS
    # -----------------------------------------------------

    Notification.objects.filter(

        vendor_id=vendor_id

    ).delete()


    messages.success(

        request,

        'All notifications cleared.'

    )


    return redirect(

        'vendor_notifications'

    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard(request):

    # -----------------------------------------------------
    # Check admin login
    # -----------------------------------------------------

    if not is_admin(request):

        return redirect('login')


    # -----------------------------------------------------
    # Open admin dashboard
    # -----------------------------------------------------

    return render(

        request,

        'dashboard/admin_dashboard.html'

    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    # -----------------------------------------------------
    # Clear session
    # -----------------------------------------------------

    request.session.flush()


    # -----------------------------------------------------
    # Redirect to login
    # -----------------------------------------------------

    return redirect('login')

# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    request.session.flush()

    return redirect('login')


# =========================================================
# VIEW USERS
# =========================================================

def view_users(request):

    # -----------------------------------------------------
    # Only Admin can access User Management
    # -----------------------------------------------------

    if not is_admin(request):

        return redirect('login')


    search = request.GET.get(
        'search',
        ''
    ).strip()


    users = User.objects.filter(
        role__in=[
            'CUSTOMER',
            'VENDOR'
        ]
    )


    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if search:

        search_filter = (

            Q(name__icontains=search) |

            Q(email__icontains=search) |

            Q(phone__icontains=search) |

            Q(address__icontains=search) |

            Q(role__icontains=search)

        )


        # Search by User ID

        if search.isdigit():

            search_filter |= Q(
                id=int(search)
            )


        users = users.filter(
            search_filter
        )


    users = users.order_by(
        'id'
    )


    context = {

        'users': users,

        'search': search,

    }


    return render(
        request,
        'dashboard/user_list.html',
        context
    )


# =========================================================
# EDIT USER
# =========================================================

def edit_user(request, user_id):

    # -----------------------------------------------------
    # Only Admin can edit users
    # -----------------------------------------------------

    if not is_admin(request):

        return redirect('login')


    user = User.objects.get(

        id=user_id,

        role__in=[
            'CUSTOMER',
            'VENDOR'
        ]

    )


    # -----------------------------------------------------
    # UPDATE USER
    # -----------------------------------------------------

    if request.method == 'POST':

        user.name = request.POST.get(
            'name',
            ''
        ).strip()

        user.email = request.POST.get(
            'email',
            ''
        ).strip().lower()

        user.phone = request.POST.get(
            'phone',
            ''
        ).strip()

        user.address = request.POST.get(
            'address',
            ''
        ).strip()

        user.role = request.POST.get(
            'role'
        )


        user.save(
            update_fields=[
                'name',
                'email',
                'phone',
                'address',
                'role'
            ]
        )


        return redirect(
            'view_users'
        )


    return render(
        request,
        'dashboard/edit_user.html',
        {
            'user': user
        }
    )


# =========================================================
# =========================================================
# DELETE USER
# =========================================================

def delete_user(request, user_id):

    # -----------------------------------------------------
    # ONLY ADMIN CAN DELETE USERS
    # -----------------------------------------------------

    if not is_admin(request):

        return redirect('login')


    # -----------------------------------------------------
    # GET CUSTOMER / VENDOR
    # -----------------------------------------------------

    user = get_object_or_404(

        User,

        id=user_id,

        role__in=[
            'CUSTOMER',
            'VENDOR'
        ]

    )


    try:

        with transaction.atomic():

            # =================================================
            # CUSTOMER
            # =================================================

            if user.role == 'CUSTOMER':

                # ---------------------------------------------
                # DELETE CART ITEMS
                # ---------------------------------------------

                CartItem.objects.filter(
                    cart__customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE CART
                # ---------------------------------------------

                Cart.objects.filter(
                    customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE WISHLIST
                # ---------------------------------------------

                Wishlist.objects.filter(
                    customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE REVIEWS
                # ---------------------------------------------

                Review.objects.filter(
                    customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE ORDER ITEMS
                # ---------------------------------------------

                OrderItem.objects.filter(
                    order__customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE PAYMENTS
                # ---------------------------------------------

                Payment.objects.filter(
                    order__customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE ORDERS
                # ---------------------------------------------

                Order.objects.filter(
                    customer=user
                ).delete()


                # ---------------------------------------------
                # DELETE USER
                # ---------------------------------------------

                user.delete()


            # =================================================
            # VENDOR
            # =================================================

            elif user.role == 'VENDOR':

                # Vendor deletion needs to be handled
                # separately because products/orders may exist.

                messages.error(
                    request,
                    'Vendor cannot be deleted while vendor products or orders exist.'
                )

                return redirect('view_users')


    except Exception as error:

        print(
            '========================================'
        )

        print(
            'DELETE USER ERROR:',
            repr(error)
        )

        print(
            '========================================'
        )

        messages.error(
            request,
            'User could not be deleted.'
        )

        return redirect('view_users')


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    messages.success(
        request,
        f'{user.name} deleted successfully.'
    )


    return redirect(
        'view_users'
    )
# =========================================================
# VENDOR PROFILE
# =========================================================

def vendor_profile(request):

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if not request.session.get('user_id'):
        return redirect('login')


    # -----------------------------------------------------
    # ONLY VENDOR
    # -----------------------------------------------------

    if request.session.get('user_role') != 'VENDOR':
        return redirect('login')


    # -----------------------------------------------------
    # GET LOGGED-IN VENDOR
    # -----------------------------------------------------

    vendor_id = request.session.get('user_id')

    try:

        vendor = User.objects.get(
            id=vendor_id,
            role='VENDOR'
        )

    except User.DoesNotExist:

        request.session.flush()

        return redirect('login')


    # =====================================================
    # SAVE PROFILE
    # =====================================================

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()

        phone = request.POST.get('phone', '').strip()

        address = request.POST.get('address', '').strip()


        # -------------------------------------------------
        # NAME VALIDATION
        # -------------------------------------------------

        if not name:

            messages.error(
                request,
                'Name cannot be empty.'
            )

            return render(
                request,
                'dashboard/vendor_profile.html',
                {
                    'vendor': vendor,
                    'edit_mode': True
                }
            )


        # -------------------------------------------------
        # UPDATE VENDOR
        # -------------------------------------------------

        vendor.name = name

        vendor.phone = phone

        vendor.address = address

        vendor.save(
            update_fields=[
                'name',
                'phone',
                'address'
            ]
        )


        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        messages.success(
            request,
            'Profile updated successfully.'
        )


        return redirect(
            'vendor_profile'
        )


    # =====================================================
    # PROFILE PAGE
    # =====================================================

    return render(
        request,
        'dashboard/vendor_profile.html',
        {
            'vendor': vendor,
            'edit_mode': request.GET.get('edit') == '1'
        }
    )