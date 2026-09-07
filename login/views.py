from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.messages import get_messages
from .models import User


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

     # -----------------------------------------------------
    # CLEAR OLD MESSAGES FROM PREVIOUS ACTIONS
    # -----------------------------------------------------

    

    
       
    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')


        # =================================================
        # ADMIN LOGIN
        # =================================================

        try:

            admin_user = DjangoUser.objects.get(
                email=email,
                is_superuser=True
            )

        except DjangoUser.DoesNotExist:

            admin_user = None


        # -------------------------------------------------
        # ADMIN FOUND
        # -------------------------------------------------

        if admin_user:

            if not admin_user.check_password(password):

                messages.error(
                    request,
                    'Invalid email or password.'
                )

                return render(
                    request,
                    'login.html'
                )


            # -------------------------------------------------
            # DJANGO ADMIN LOGIN
            # -------------------------------------------------

            auth_login(
                request,
                admin_user
            )


            # -------------------------------------------------
            # STORE ADMIN SESSION
            # -------------------------------------------------

            request.session['user_id'] = admin_user.id

            request.session['user_name'] = admin_user.username

            request.session['user_role'] = 'ADMIN'

            request.session['user_email'] = admin_user.email


            # -------------------------------------------------
            # ADMIN DASHBOARD
            # -------------------------------------------------

            return redirect(
                'admin_dashboard'
            )


        # =================================================
        # CUSTOMER / VENDOR LOGIN
        # =================================================

        try:

            user = User.objects.get(
                email=email
            )
            print("================================")
            print("LOGIN EMAIL:", email)
            print("USER EMAIL:", user.email)
            print("USER ROLE:", user.role)
            print("STORED PASSWORD:", user.password)
            print(
                  "PASSWORD MATCH:",
                check_password(password, user.password)
            )
            print("================================")

        except User.DoesNotExist:

            messages.error(
                request,
                'Invalid email or password.'
            )

            return render(
                request,
                'login.html'
            )


        # =================================================
        # CHECK CUSTOMER / VENDOR PASSWORD
        # =================================================

        if not check_password(
            password,
            user.password
        ):

            messages.error(
                request,
                'Invalid email or password.'
            )

            return render(
                request,
                'login.html'
            )


        # =================================================
        # STORE SESSION
        # =================================================

        request.session['user_id'] = user.id

        request.session['user_name'] = user.name

        request.session['user_role'] = user.role

        request.session['user_email'] = user.email


        # =================================================
        # CUSTOMER
        # =================================================

        if user.role == 'CUSTOMER':

            return redirect(
                'customer_dashboard'
            )


        # =================================================
        # VENDOR
        # =================================================

        elif user.role == 'VENDOR':

            return redirect(
                'vendor_dashboard'
            )


        # =================================================
        # INVALID ROLE
        # =================================================

        messages.error(
            request,
            'Invalid user role.'
        )

        return render(
            request,
            'login.html'
        )


    # =====================================================
    # GET REQUEST
    # =====================================================

    return render(
        request,
        'login.html'
    )



# =========================================================
# FORGOT PASSWORD
# =========================================================

# =========================================================
# FORGOT PASSWORD
# =========================================================

def forgot_password(request):

    # -----------------------------------------------------
    # CLEAR OLD MESSAGES
    # -----------------------------------------------------
    # This prevents old cart/order messages from appearing
    # on the Forgot Password page.

    

    # =====================================================
    # POST REQUEST
    # =====================================================

    if request.method == 'POST':

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        email = request.POST.get(
            'email',
            ''
        ).strip().lower()

        new_password = request.POST.get(
            'new_password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )


        # -------------------------------------------------
        # CHECK EMAIL
        # -------------------------------------------------

        if not email:

            messages.error(
                request,
                'Please enter your registered email.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        if not new_password:

            messages.error(
                request,
                'Please enter a new password.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # -------------------------------------------------
        # CHECK PASSWORD MATCH
        # -------------------------------------------------

        if new_password != confirm_password:

            messages.error(
                request,
                'New password and confirm password do not match.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # -------------------------------------------------
        # CHECK PASSWORD LENGTH
        # -------------------------------------------------

        if len(new_password) < 6:

            messages.error(
                request,
                'Password must be at least 6 characters.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # =================================================
        # FIND USER
        # =================================================

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            messages.error(
                request,
                'No account found with this email.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # =================================================
        # CUSTOMER / VENDOR ONLY
        # =================================================

        if user.role not in ['CUSTOMER', 'VENDOR']:

            messages.error(
                request,
                'Password reset is not available for this account.'
            )

            return render(
                request,
                'forgot_password.html'
            )


        # =================================================
        # HASH NEW PASSWORD
        # =================================================

        user.password = make_password(
            new_password
        )


        # =================================================
        # SAVE PASSWORD
        # =================================================

        user.save(
            update_fields=['password']
        )


        # =================================================
        # SUCCESS
        # =================================================

        messages.success(
            request,
            'Password reset successfully. Please login with your new password.'
        )


        # =================================================
        # GO TO LOGIN
        # =================================================

        return redirect(
            'login'
        )


    # =====================================================
    # GET REQUEST
    # =====================================================

    return render(
        request,
        'forgot_password.html'
    )