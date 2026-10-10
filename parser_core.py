import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse

DELAY_MIN = 1.5
DELAY_MAX = 3.5
TIMEOUT = 15

TOUR_KEYWORDS = [
    '3d тур', '3д тур', '3d-тур', '3д-тур',
    'виртуальный тур', 'виртуальный 3d',
    '360°', '360 градус', 'панорам',
    'virtual tour', 'matterport', 'pano2vr', '3d-vizor',
    'kuula.co', 'roundme', 'veer.tv'
]

TOUR_HOSTS = [
    'matterport.com', '3d-vizor.ru', 'pano2vr',
    'kuula.co', 'roundme.com', 'my.matterport',
    'sketchfab.com', 'veervr.tv', '720yun.com'
]

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
}

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(
    r'(?:\+7|8)[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}'
)


def has_3d_tour(html, soup):
    low = html.lower()
    if any(kw in low for kw in TOUR_KEYWORDS):
        return True
    for tag in soup.find_all(['iframe', 'script', 'embed', 'object']):
        src = (tag.get('src') or tag.get('data') or '') + str(tag)
        if any(host in src.lower() for host in TOUR_HOSTS):
            return True
    return False


def extract_contacts(html, soup):
    emails = set(EMAIL_RE.findall(html))
    for a in soup.find_all('a', href=True):
        if a['href'].lower().startswith('mailto:'):
            emails.add(a['href'].split(':', 1)[1].split('?')[0])

    bad = ('example.com', 'sentry.io', 'wixpress.com', '.png', '.jpg')
    emails = [e for e in emails if not any(b in e.lower() for b in bad)]

    text = soup.get_text(" ", strip=True)
    phones = PHONE_RE.findall(text)
    title = soup.title.get_text(strip=True) if soup.title else ''

    return {
        'email': emails[0] if emails else '',
        'all_emails': '; '.join(sorted(emails)),
        'phone': phones[0] if phones else '',
        'title': title,
    }


def guess_city(title):
    m = re.search(r'[,–\-—]\s*([А-ЯЁ][а-яё\-]+)\s*$', title)
    return m.group(1) if m else ''


def check_one(url):
    """Проверяет один URL. Возвращает dict с результатом."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        if not r.encoding or r.encoding.lower() == 'iso-8859-1':
            r.encoding = r.apparent_encoding
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')

        has_tour = has_3d_tour(html, soup)
        contacts = extract_contacts(html, soup)
        city = guess_city(contacts['title'])
        domain = urlparse(url).netloc

        return {
            'url': url,
            'domain': domain,
            'title': contacts['title'],
            'city': city,
            'has_tour': 'Да' if has_tour else 'Нет',
            'email': contacts['email'],
            'all_emails': contacts['all_emails'],
            'phone': contacts['phone'],
            'status': 'ок',
        }
    except requests.exceptions.HTTPError as e:
        return {'url': url, 'status': f'HTTP ошибка: {e}', 'has_tour': '?'}
    except requests.exceptions.RequestException as e:
        return {'url': url, 'status': f'Ошибка сети: {e}', 'has_tour': '?'}
    except Exception as e:
        return {'url': url, 'status': f'Ошибка: {e}', 'has_tour': '?'}


def check_urls(urls, on_progress=None):
    """Проверяет список URL. Если передан on_progress — вызывает его после каждой ссылки."""
    results = []
    total = len(urls)
    for i, url in enumerate(urls, 1):
        res = check_one(url)
        results.append(res)
        if on_progress:
            on_progress(i, total, res)
        if i < total:
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    return results