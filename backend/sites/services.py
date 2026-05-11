from .models import Site

class SiteService:
    """Public API for the sites module."""

    def create_site(self, user_id: int, domain: str) -> Site:
        if Site.objects.filter(user_id=user_id, domain=domain).exists():
            raise ValueError('You already have a site with this domain.')
        return Site.objects.create(user_id=user_id, domain=domain)

    def get_sites_for_user(self, user_id: int):
        return Site.objects.filter(user_id=user_id, is_active=True).order_by('-created_at')

    def get_site_by_id(self, site_id: int) -> Site | None:
        try:
            return Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            return None

    def get_site_by_token(self, token: str) -> Site | None:
        """Used by the tracking module."""
        try:
            return Site.objects.get(tracking_token=token, is_active=True)
        except Site.DoesNotExist:
            return None

    def update_site(self, site_id: int, user_id: int, domain=None, is_active=None) -> Site | None:
        site = self.get_site_by_id(site_id)
        if not site or site.user.id != user_id:
            return None
        if domain is not None:
            # Check uniqueness excluding current site
            if Site.objects.filter(user_id=user_id, domain=domain).exclude(id=site_id).exists():
                raise ValueError('You already have a site with this domain.')
            site.domain = domain
        if is_active is not None:
            site.is_active = is_active
        site.save()
        return site

    def deactivate_site(self, site_id: int, user_id: int) -> bool:
        """Soft delete."""
        return self.update_site(site_id, user_id, is_active=False) is not None
    
    def get_all_active_sites(self):
        """Fetch all active sites for aggreggation"""
        return Site.objects.filter(is_active=True)