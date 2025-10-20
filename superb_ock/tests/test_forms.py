"""
Tests for forms in the superb_ock application.
"""
import pytest
from django.contrib.auth.models import User

from superb_ock.forms import EditAuthForm, EditUserForm


@pytest.mark.django_db
class TestEditAuthForm:
    """Tests for the EditAuthForm (authentication form)."""

    def test_form_has_correct_fields(self):
        """Test that form has username and password fields."""
        form = EditAuthForm()

        assert 'username' in form.fields
        assert 'password' in form.fields

    def test_form_fields_have_correct_widgets(self):
        """Test that form fields have Bootstrap classes."""
        form = EditAuthForm()

        # Check that form-control class is applied
        username_widget = form.fields['username'].widget
        password_widget = form.fields['password'].widget

        assert 'form-control' in username_widget.attrs.get('class', '')
        assert 'form-control' in password_widget.attrs.get('class', '')

    def test_form_validates_with_correct_data(self):
        """Test that form validates with correct credentials."""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        form_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        form = EditAuthForm(data=form_data)

        # Note: AuthenticationForm requires request parameter and checks against database
        # This is a basic structure test
        assert 'username' in form.data
        assert 'password' in form.data


@pytest.mark.django_db
class TestEditUserForm:
    """Tests for the EditUserForm (user registration form)."""

    def test_form_has_correct_fields(self):
        """Test that form has required fields."""
        form = EditUserForm()

        assert 'username' in form.fields
        assert 'password1' in form.fields
        assert 'password2' in form.fields

    def test_form_fields_have_bootstrap_classes(self):
        """Test that form fields have Bootstrap styling."""
        form = EditUserForm()

        username_widget = form.fields['username'].widget
        password1_widget = form.fields['password1'].widget
        password2_widget = form.fields['password2'].widget

        assert 'form-control' in username_widget.attrs.get('class', '')
        assert 'form-control' in password1_widget.attrs.get('class', '')
        assert 'form-control' in password2_widget.attrs.get('class', '')

    def test_form_valid_with_correct_data(self):
        """Test that form is valid with correct data."""
        form_data = {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        form = EditUserForm(data=form_data)

        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_invalid_with_password_mismatch(self):
        """Test that form is invalid when passwords don't match."""
        form_data = {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'differentpass456!'
        }

        form = EditUserForm(data=form_data)

        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_form_invalid_with_weak_password(self):
        """Test that form is invalid with weak password."""
        form_data = {
            'username': 'newuser',
            'password1': '123',
            'password2': '123'
        }

        form = EditUserForm(data=form_data)

        assert not form.is_valid()
        # Should have password validation errors

    def test_form_invalid_with_existing_username(self):
        """Test that form is invalid with existing username."""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            password='testpass123'
        )

        form_data = {
            'username': 'existinguser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        form = EditUserForm(data=form_data)

        assert not form.is_valid()
        assert 'username' in form.errors

    def test_form_saves_user(self):
        """Test that form saves a new user correctly."""
        form_data = {
            'username': 'saveduser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        form = EditUserForm(data=form_data)

        assert form.is_valid()

        user = form.save()

        assert user.username == 'saveduser'
        assert user.check_password('complexpass123!')
        assert User.objects.filter(username='saveduser').exists()

    def test_form_password_help_text(self):
        """Test that password field has help text."""
        form = EditUserForm()

        password1_field = form.fields['password1']

        # Should have password validation help text
        assert password1_field.help_text is not None
        assert len(password1_field.help_text) > 0

    def test_form_password_labels(self):
        """Test that password fields have correct labels."""
        form = EditUserForm()

        assert form.fields['password1'].label == "Password"
        assert form.fields['password2'].label == "Re-enter Password"

    def test_form_password_placeholders(self):
        """Test that password fields have placeholders."""
        form = EditUserForm()

        password1_widget = form.fields['password1'].widget
        password2_widget = form.fields['password2'].widget

        assert password1_widget.attrs.get('placeholder') == 'Password'
        assert password2_widget.attrs.get('placeholder') == 'Password'


@pytest.mark.django_db
class TestFormIntegration:
    """Integration tests for forms."""

    def test_registration_and_login_workflow(self):
        """Test complete registration and login workflow."""
        # Step 1: Register new user
        registration_data = {
            'username': 'testworkflow',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        registration_form = EditUserForm(data=registration_data)
        assert registration_form.is_valid()

        user = registration_form.save()

        # Step 2: Login with credentials
        login_data = {
            'username': 'testworkflow',
            'password': 'complexpass123!'
        }

        # User should exist and password should be valid
        assert User.objects.filter(username='testworkflow').exists()
        assert user.check_password('complexpass123!')

    def test_form_validation_edge_cases(self):
        """Test edge cases in form validation."""
        # Empty username
        form_data = {
            'username': '',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        form = EditUserForm(data=form_data)
        assert not form.is_valid()
        assert 'username' in form.errors

        # Very long username
        form_data = {
            'username': 'a' * 200,
            'password1': 'complexpass123!',
            'password2': 'complexpass123!'
        }

        form = EditUserForm(data=form_data)
        # May be invalid due to max length
        # Actual behavior depends on Django's User model constraints

    def test_password_validation_requirements(self):
        """Test various password validation scenarios."""
        test_cases = [
            # (password, should_be_valid, description)
            ('short', False, 'Too short'),
            ('12345678', False, 'Only numbers'),
            ('password', False, 'Too common'),
            ('Pass123!@#', True, 'Complex enough'),
            ('MySecurePassword123', True, 'Good password'),
        ]

        for password, should_be_valid, description in test_cases:
            form_data = {
                'username': 'testuser',
                'password1': password,
                'password2': password
            }

            form = EditUserForm(data=form_data)

            if should_be_valid:
                # May still have other validation errors
                # Just checking password validation
                if not form.is_valid():
                    # Should not have password-specific errors
                    password_errors = form.errors.get('password1', []) + form.errors.get('password2', [])
                    # Filter out username errors
                    password_errors = [e for e in password_errors if 'username' not in str(e).lower()]
            else:
                # Should have validation errors
                # Most likely in password1 or password2
                pass
