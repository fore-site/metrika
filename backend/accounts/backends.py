from django.contrib.auth.backends import ModelBackend

class CustomModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        # Must be active (verified) AND not suspended
        if user.is_suspended:
            return False
        return super().user_can_authenticate(user)