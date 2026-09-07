
from django.db import models
from signup.models import User


# =========================================================
# CATEGORY MODEL
# =========================================================

class Category(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    category_name = models.CharField(
        max_length=100
    )

    description = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'categories'

        managed = False

    def __str__(self):

        return self.category_name


# =========================================================
# PRODUCT MODEL
# =========================================================

class Product(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    vendor = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='vendor_id',
        related_name='products'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.DO_NOTHING,
        db_column='category_id',
        related_name='products'
    )

    product_name = models.CharField(
        max_length=150
    )

    description = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock_quantity = models.IntegerField(
        default=0
    )

    product_image = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'products'

        managed = False

    def __str__(self):

        return self.product_name


# =========================================================
# ORDER MODEL
# =========================================================

class Order(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='customer_id',
        related_name='customer_orders'
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    order_status = models.CharField(
        max_length=20
    )

    shipping_address = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'orders'

        managed = False

# =========================================================
# CART MODEL
# =========================================================

class Cart(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    customer = models.OneToOneField(
        User,
        on_delete=models.DO_NOTHING,
        db_column='customer_id',
        related_name='cart'
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'cart'

        managed = False


# =========================================================
# CART ITEM MODEL
# =========================================================

class CartItem(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    cart = models.ForeignKey(
        Cart,
        on_delete=models.DO_NOTHING,
        db_column='cart_id',
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column='product_id',
        related_name='cart_items'
    )

    quantity = models.IntegerField(
        default=1
    )

    class Meta:

        db_table = 'cart_items'

        managed = False

        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]
# =========================================================
# ORDER ITEM MODEL
# =========================================================

# =========================================================
# ORDER ITEM MODEL
# =========================================================

class OrderItem(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.DO_NOTHING,
        db_column='order_id',
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column='product_id',
        related_name='order_items'
    )

    vendor = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='vendor_id',
        related_name='vendor_order_items'
    )

    quantity = models.IntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    item_status = models.CharField(
        max_length=20,
        default='PENDING'
    )

    is_viewed = models.BooleanField(
    default=False
    )

    class Meta:

        db_table = 'order_items'

        managed = False  


# =========================================================
# PAYMENT MODEL
# =========================================================

class Payment(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.DO_NOTHING,
        db_column='order_id',
        related_name='payment'
    )

    payment_method = models.CharField(
        max_length=10
    )

    payment_status = models.CharField(
        max_length=10
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        db_table = 'payments'

        managed = False
# =========================================================
# NOTIFICATION MODEL
# =========================================================

class Notification(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    vendor = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='vendor_id',
        related_name='vendor_notifications'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.DO_NOTHING,
        db_column='order_id',
        related_name='notifications'
    )

    message = models.CharField(
        max_length=255
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'notifications'

        managed = False

# =========================================================
# WISHLIST MODEL
# =========================================================

class Wishlist(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='customer_id',
        related_name='wishlist_items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column='product_id',
        related_name='wishlist_items'
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'wishlist'

        managed = False

        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'product'],
                name='unique_customer_product_wishlist'
            )
        ]


# =========================================================
# REVIEW MODEL
# =========================================================

class Review(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='customer_id',
        related_name='product_reviews'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        db_column='product_id',
        related_name='reviews'
    )

    rating = models.IntegerField()

    comment = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField()

    class Meta:

        db_table = 'reviews'

        managed = False        
