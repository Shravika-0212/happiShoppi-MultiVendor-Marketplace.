from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from .models import User


def signup_view(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        role = request.POST.get('role')

        # Remove unnecessary spaces
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip() if phone else ''
        address = address.strip() if address else ''

        # Check password confirmation
        if password != confirm_password:
            messages.error(
                request,
                'Passwords do not match.'
            )
            return render(request, 'signup.html')

        # Check duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                'An account with this email already exists.'
            )
            return render(request, 'signup.html')

        # Check valid role
        if role not in ['CUSTOMER', 'VENDOR']:
            messages.error(
                request,
                'Please select a valid role.'
            )
            return render(request, 'signup.html')

        # Hash password
        hashed_password = make_password(password)

        # Save user
        User.objects.create(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            phone=phone if phone else None,
            address=address if address else None
        )

        # Admin added the user
        if request.GET.get('from_admin') == '1':

            messages.success(
                request,
                'User added successfully.'
            )

            return redirect('view_users')

        # Normal signup
        messages.success(
            request,
            'Account created successfully. Please login.'
        )

        return redirect('login')

    return render(request, 'signup.html')