"""
Authentication views for user signup, login, and logout.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from ..forms import EditUserForm, EditAuthForm


def signUpUser(request):
    """
    Handle user registration.

    GET: Display signup form
    POST: Create new user account
    """
    if request.method == "GET":
        return render(
            request, "superb_ock/auth/signUpUser.html", {"form": EditUserForm()}
        )

    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"]
                )
                user.save()
                login(request, user)

                # Store flag in session to show welcome modal
                request.session['show_welcome_modal'] = True

                return redirect("home")
            except IntegrityError:
                return render(
                    request,
                    "superb_ock/auth/signUpUser.html",
                    {"form": EditUserForm(), "error": "Username Already Taken"},
                )

        else:
            return render(
                request,
                "superb_ock/auth/signUpUser.html",
                {"form": EditUserForm(), "error": "Passwords did not match"},
            )


def logOutUser(request):
    """Handle user logout."""
    logout(request)
    return redirect("home")


def logInUser(request):
    """
    Handle user login.

    GET: Display login form
    POST: Authenticate user
    """
    if request.method == "GET":
        return render(request, "superb_ock/auth/login.html", {"form": EditAuthForm()})

    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user == None:
            return render(
                request,
                "superb_ock/auth/login.html",
                {"form": EditAuthForm(), "error": "Unknown User / Incorrect Password"},
            )
        else:
            login(request, user)
            return redirect("home")
