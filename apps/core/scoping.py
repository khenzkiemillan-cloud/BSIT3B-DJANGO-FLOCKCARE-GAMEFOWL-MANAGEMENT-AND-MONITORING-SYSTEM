from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.info.models import FlockMember


def scoped_flock_members(user):
    return FlockMember.objects.filter(user=user)


def scoped_flock_member(user, pk):
    """Return one of the user's flock members, or raise ``Http404``.

    Invalid primary keys (for example a non-numeric POST value) are treated as
    "not found" rather than surfacing as a server error.
    """
    try:
        return get_object_or_404(scoped_flock_members(user), pk=pk)
    except (TypeError, ValueError) as exc:
        raise Http404('Flock member not found.') from exc


# Aliases to match your views expectations
scoped_infos = scoped_flock_members
scoped_info = scoped_flock_member
