from urllib.parse import urlparse

SEARCH_ENGINES = {
    # Global
    'google':      'Google',
    'bing':        'Bing',
    'yahoo':       'Yahoo',
    'duckduckgo':  'DuckDuckGo',
    'ecosia':      'Ecosia',
    'ask':         'Ask',
    'aol':         'AOL',
    'qwant':       'Qwant',

    # Russia / Eastern Europe
    'yandex':      'Yandex',
    'rambler':     'Rambler',
    'mail.ru':     'Mail.ru',

    # Asia
    'baidu':       'Baidu',
    'sogou':       'Sogou',
    'so.com':      '360 Search',
    'shenma':      'Shenma',
    'naver':       'Naver',
    'daum':        'Daum',
    'seznam':      'Seznam',
    'szukacz':     'Szukacz',

    # Middle East / Africa
    'araby':       'Araby',
    'yandex.com.tr': 'Yandex Turkey',
    'mywebsearch': 'MyWebSearch',
}

SOCIAL_DOMAINS = {
    'facebook.com':      'Facebook',
    'instagram.com':     'Instagram',
    'twitter.com':       'Twitter',
    'x.com':             'X',
    'linkedin.com':      'LinkedIn',
    'reddit.com':        'Reddit',
    'pinterest.com':     'Pinterest',
    'tiktok.com':        'TikTok',
    'snapchat.com':      'Snapchat',
    'tumblr.com':        'Tumblr',
    'whatsapp.com':      'WhatsApp',
    'telegram.org':      'Telegram',
    'vk.com':            'VKontakte',
    'ok.ru':             'Odnoklassniki',
    'discord.com':       'Discord',
    'twitch.tv':         'Twitch',
    'youtube.com':       'YouTube',
    'youtu.be':          'YouTube',
    'quora.com':         'Quora',
    'medium.com':        'Medium',
    'github.com':        'GitHub',
    'stackoverflow.com': 'Stack Overflow',
    'stackexchange.com': 'Stack Exchange',
    'flickr.com':        'Flickr',
    'dribbble.com':      'Dribbble',
    'behance.net':       'Behance',
    'news.ycombinator.com': 'Hacker News',
    'producthunt.com':   'Product Hunt',
    'weibo.com':         'Weibo',
    'zhihu.com':         'Zhihu',
    'douyin.com':        'Douyin',
    'kuaishou.com':      'Kuaishou',
    'line.me':           'Line',
    'utreon.com':        'Utreon',
}

# Parsing function
def parse_referrer(referrer_url: str) -> tuple[str, str]:
    """
    Return (source, medium) derived from the referrer URL.

    Medium values:
        - 'organic'  → from a known search engine
        - 'social'   → from a known social network / platform
        - 'referral' → from any other external URL
        - 'none'     → direct / no referrer (source = 'Direct')
    """
    if not referrer_url:
        return ('Direct', 'none')

    try:
        parsed = urlparse(referrer_url)
    except Exception:
        return ('', 'referral')

    hostname = (parsed.hostname or '').lower().removeprefix('www.')

    for key, name in SEARCH_ENGINES.items():
        if key in hostname:
            return (name, 'organic')

    for domain, name in SOCIAL_DOMAINS.items():
        if hostname == domain or hostname.endswith('.' + domain):
            return (name, 'social')

    return (hostname, 'referral')