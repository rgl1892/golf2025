"""
Component Showcase View

Development-only view for displaying all reusable components and design patterns.
Useful for:
- Documenting components
- Testing component appearance
- Ensuring design consistency
- Onboarding new developers
"""

from django.shortcuts import render
from django.conf import settings
from django.http import Http404


def component_showcase(request):
    """
    Display all reusable components and design patterns.
    Only available in DEBUG mode.
    """
    if not settings.DEBUG:
        raise Http404("Component showcase is only available in development mode")

    # Sample data for component demonstrations
    context = {
        'title': 'Component Showcase',

        # Toast notification examples
        'toast_examples': [
            {'type': 'success', 'message': 'Round saved successfully!'},
            {'type': 'error', 'message': 'Failed to save round'},
            {'type': 'warning', 'message': 'Please complete all holes'},
            {'type': 'info', 'message': 'Round is in progress'}
        ],

        # Empty state examples
        'empty_state_examples': [
            {
                'title': 'No rounds yet',
                'icon': 'golf-ball',
                'description': 'Create your first round to get started!',
                'cta_url': 'new_round',
                'cta_text': 'Create Round'
            },
            {
                'title': 'No highlights',
                'icon': 'video',
                'description': 'Upload highlight videos to showcase your best shots.',
                'cta_url': None,
                'cta_text': 'Upload Highlight'
            },
            {
                'title': 'No players found',
                'icon': 'user',
                'description': 'Add players to start tracking scores.',
                'cta_url': None,
                'cta_text': None
            }
        ],

        # CSS Variables
        'css_variables': {
            'Colors': [
                ('--color-primary', '#007bff', 'Primary brand color'),
                ('--color-success', '#28a745', 'Success state'),
                ('--color-danger', '#dc3545', 'Error state'),
                ('--color-warning', '#ffc107', 'Warning state'),
            ],
            'Spacing': [
                ('--space-xs', '4px', 'Extra small spacing'),
                ('--space-sm', '8px', 'Small spacing'),
                ('--space-md', '16px', 'Medium spacing'),
                ('--space-lg', '24px', 'Large spacing'),
                ('--space-xl', '32px', 'Extra large spacing'),
            ],
            'Shadows': [
                ('--shadow-sm', '0 2px 4px rgba(0,0,0,0.1)', 'Small shadow'),
                ('--shadow-md', '0 4px 8px rgba(0,0,0,0.15)', 'Medium shadow'),
                ('--shadow-lg', '0 8px 16px rgba(0,0,0,0.2)', 'Large shadow'),
            ]
        },

        # JavaScript modules
        'js_modules': [
            {
                'name': 'Toast Notifications',
                'file': 'toast.js',
                'description': 'Display temporary notification messages to users',
                'usage': 'window.toast.success("Message")',
                'methods': ['success()', 'error()', 'warning()', 'info()']
            },
            {
                'name': 'Video Player',
                'file': 'video-player.js',
                'description': 'Manage video playback in modals',
                'usage': 'videoPlayer.play(url, title)',
                'methods': ['play()', 'preload()', 'cleanup()']
            },
            {
                'name': 'Lazy Loading',
                'file': 'lazy-loading.js',
                'description': 'Lazy load images and videos for better performance',
                'usage': '<img data-src="image.jpg" loading="lazy">',
                'methods': ['observeNewElements()', 'disconnect()']
            },
            {
                'name': 'Accessibility',
                'file': 'accessibility.js',
                'description': 'Keyboard navigation and screen reader support',
                'usage': 'window.a11y.registerShortcut(key, callback, desc)',
                'methods': ['registerShortcut()', 'announce()', 'trapFocus()']
            },
            {
                'name': 'Form Validation',
                'file': 'form-validation.js',
                'description': 'Real-time form validation with Bootstrap integration',
                'usage': 'new FormValidator("#form", options)',
                'methods': ['validate()', 'validateField()', 'showError()']
            }
        ],

        # Keyboard shortcuts
        'keyboard_shortcuts': [
            {'key': '?', 'action': 'Show keyboard shortcuts help'},
            {'key': 'A / ←', 'action': 'Previous round'},
            {'key': 'D / →', 'action': 'Next round'},
            {'key': 'H', 'action': 'Go to home'},
            {'key': 'Esc', 'action': 'Close modal/dialog'},
        ]
    }

    return render(request, 'superb_ock/showcase.html', context)
