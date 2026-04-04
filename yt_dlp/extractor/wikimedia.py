import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    get_element_by_class,
    int_or_none,
    parse_qs,
    remove_start,
    unescapeHTML,
    urljoin,
)
from ..utils.traversal import traverse_obj
from ..version import __version__


class WikimediaIE(InfoExtractor):
    IE_NAME = 'wikimedia.org'
    _VALID_URL = r'https?://commons\.wikimedia\.org/wiki/File:(?P<id>[^/#?]+)\.\w+'
    _TESTS = [{
        'url': 'https://commons.wikimedia.org/wiki/File:Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS.webm',
        'info_dict': {
            'url': 're:https?://upload.wikimedia.org/wikipedia',
            'ext': 'webm',
            'id': 'Die_Temperaturkurve_der_Erde_(ZDF,_Terra_X)_720p_HD_50FPS',
            'title': 'Die Temperaturkurve der Erde (ZDF, Terra X) 720p HD 50FPS.webm - Wikimedia Commons',
            'description': 'md5:7cd84f76e7081f1be033d0b155b4a460',
            'license': 'Creative Commons Attribution 4.0 International',
            'uploader': 'ZDF/Terra X/Gruppe 5/Luise Wagner, Jonas Sichert, Andreas Hougardy',
            'subtitles': 'count:4',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        user_agent = f'yt-dlp/{__version__} (https://github/yt-dlp/yt-dlp)'
        webpage = self._download_webpage(url, video_id, headers={'User-Agent': user_agent})

        formats = []
        seen_urls = set()
        for fmt in set(re.findall(r'<source\s*src=["\'][^"]+"[^>]+>', unescapeHTML(webpage))):
            attr = extract_attributes(fmt)
            fmt_url = attr.get('src')
            if not fmt_url or fmt_url in seen_urls:
                continue
            seen_urls.add(fmt_url)
            formats.append({
                'url': fmt_url,
                'ext': determine_ext(fmt_url),
                **traverse_obj(attr, ({
                    'height': ('data-height', {int_or_none}),
                    'width': ('data-width', {int_or_none}),
                }),
                )})

        subtitles = {}
        for sub in set(re.findall(r'\bsrc\s*=\s*["\'](/w/api[^"]+)["\']', webpage)):
            sub = urljoin('https://commons.wikimedia.org', unescapeHTML(sub))
            qs = parse_qs(sub)
            lang = qs.get('lang', [None])[-1]
            sub_ext = qs.get('trackformat', [None])[-1]
            if lang and sub_ext:
                subtitles.setdefault(lang, []).append({'ext': sub_ext, 'url': sub})

        return {
            'id': video_id,
            'description': clean_html(get_element_by_class('description', webpage)),
            'title': remove_start(self._og_search_title(webpage), 'File:'),
            'license': self._html_search_regex(
                r'licensed under(?: the)? (.+?) license',
                get_element_by_class('licensetpl', webpage), 'license', default=None),
            'uploader': self._html_search_regex(
                r'>\s*Author\s*</td>\s*<td\b[^>]*>\s*([^<]+)\s*</td>', webpage, 'video author', default=None),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': {
                'User-Agent': user_agent,
            },
        }
