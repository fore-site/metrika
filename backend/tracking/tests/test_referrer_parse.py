from django.test import SimpleTestCase
from tracking.referrer import parse_referrer   # your module

class UTMHandlingTests(SimpleTestCase):
    def test_utm_source_medium_overrides_referrer(self):
        source, medium = parse_referrer(
            referrer_url='https://google.com/search?q=test',
            page_url='https://example.com/page?utm_source=newsletter&utm_medium=email'
        )
        self.assertEqual(source, 'newsletter')
        self.assertEqual(medium, 'email')

    def test_utm_source_only_ignored(self):
        source, medium = parse_referrer(
            referrer_url='https://google.com',
            page_url='https://example.com?utm_source=blog'
        )
        # utm_medium missing → fall back to referrer parsing
        self.assertEqual(source, 'Google')
        self.assertEqual(medium, 'organic')

    def test_no_utm_uses_referrer(self):
        source, medium = parse_referrer(
            referrer_url='https://twitter.com/share',
            page_url='https://example.com/page'
        )
        self.assertEqual(source, 'Twitter')
        self.assertEqual(medium, 'social')

    def test_direct_with_utm_is_campaign(self):
        source, medium = parse_referrer(
            referrer_url='',
            page_url='https://example.com/?utm_source=ad&utm_medium=cpc'
        )
        self.assertEqual(source, 'ad')
        self.assertEqual(medium, 'cpc')