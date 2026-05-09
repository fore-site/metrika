import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from rest_framework import serializers


class SymbolPasswordValidator:
    """Require at least one uppercase letter, one digit, and one special character."""
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_("Password must contain at least one uppercase letter."))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_("Password must contain at least one digit."))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_("Password must contain at least one special character."))

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter, one digit, and one special character.")


def validate_name_field(value):
    """ Validate name passed into into register view or name change view."""
    # Strip leading/trailing whitespace and collapse internal spaces
    cleaned = ' '.join(value.split())
    if not cleaned:
        raise serializers.ValidationError("Name cannot be blank.")
        # Length check (min 2)
    if len(cleaned) < 2:
        raise serializers.ValidationError("Name must be at least 2 characters.")
        # Character validation: allow letters (any language), digits, spaces, hyphens, apostrophes, periods, commas
    if not re.match(r'^[\w\s\-.,\']+$', cleaned, re.UNICODE):
        raise serializers.ValidationError("Name contains invalid characters.")
    return cleaned


# Regex for validating domain names (simplified, allows subdomains)
HOSTNAME_REGEX = re.compile(
    r'^(?!\-)[A-Za-z0-9\-]{1,63}(?<!\-)'
    r'(\-(?!\-))?'
    r'(\.[A-Za-z]{2,})+$'
)

def validate_domain(value: str) -> str:
    """
    Normalize and validate a domain name.
    Returns the cleaned domain string.
    """
    domain = value.strip().lower().rstrip('/')

    if not domain:
        raise serializers.ValidationError("Domain cannot be empty.")

    # Reject any protocol or path
    if '://' in domain or '/' in domain:
        raise serializers.ValidationError(
            "Enter only the domain name (e.g. example.com), without http:// or paths."
        )

    if not HOSTNAME_REGEX.match(domain):
        raise serializers.ValidationError("Enter a valid domain name (e.g. example.com).")

    return domain
