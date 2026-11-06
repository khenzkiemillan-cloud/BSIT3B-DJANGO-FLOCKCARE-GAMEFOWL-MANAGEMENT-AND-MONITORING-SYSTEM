from django.shortcuts import redirect


def home(request):
    """Send the project root to the flock dashboard."""
    return redirect('dashboard')
