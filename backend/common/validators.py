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
        # Disallow leading/trailing punctuation
    if re.match(r'^[-.,\']', cleaned) or re.search(r'[-.,\']$', cleaned):
        raise serializers.ValidationError("Name cannot start or end with punctuation.")
        # Disallow leading or trailing digits
    if not cleaned[0].isalpha() or not cleaned[-1].isalpha():
        raise serializers.ValidationError("Name must start and end with a letter.")
    return cleaned