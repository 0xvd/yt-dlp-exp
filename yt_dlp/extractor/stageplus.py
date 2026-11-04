import json
import uuid

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    filter_dict,
    float_or_none,
    traverse_obj,
    try_call,
    unified_timestamp,
    url_or_none,
)


class StagePlusVODConcertIE(InfoExtractor):
    _NETRC_MACHINE = 'stageplus'
    _VALID_URL = r'https?://(?:www\.)?stage-plus\.com/video/(?P<id>(?:vod_concert|video)_\w+)'
    _TESTS = [{
        'url': 'https://www.stage-plus.com/video/vod_concert_APNM8GRFDPHMASJKBSPJACG',
        'playlist_count': 6,
        'info_dict': {
            'id': 'vod_concert_APNM8GRFDPHMASJKBSPJACG',
            'title': 'Yuja Wang plays Rachmaninoff\'s Piano Concerto No. 2',
            'description': 'md5:50f78ec180518c9bdb876bac550996fc',
            'artists': ['Yuja Wang', 'Lorenzo Viotti'],
            'upload_date': '20230331',
            'timestamp': 1680249600,
            'release_date': '20210709',
            'release_timestamp': 1625788800,
            'thumbnails': 'count:3',
        },
        'playlist': [{
            'info_dict': {
                'id': 'performance_work_A1IN4PJFE9MM2RJ3CLBMUSJBBSOJAD9O',
                'ext': 'mp4',
                'title': 'Piano Concerto No. 2 in C Minor, Op. 18',
                'description': 'md5:50f78ec180518c9bdb876bac550996fc',
                'upload_date': '20230331',
                'timestamp': 1680249600,
                'release_date': '20210709',
                'release_timestamp': 1625788800,
                'duration': 2207,
                'chapters': 'count:5',
                'artists': ['Yuja Wang'],
                'composers': ['Sergei Rachmaninoff'],
                'album': 'Yuja Wang plays Rachmaninoff\'s Piano Concerto No. 2 – from Odeonsplatz',
                'album_artists': ['Yuja Wang', 'Lorenzo Viotti'],
                'track': 'Piano Concerto No. 2 in C Minor, Op. 18',
                'track_number': 1,
                'genre': 'Instrumental Concerto',
            },
        }],
        'skip': 'Account and Subscription Required',
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://www.stage-plus.com/video/video_APKM8PBFBSR30DO',
        'info_dict': {
            'id': 'video_APKM8PBFBSR30DO',
            'ext': 'mp4',
            'title': 'Saint-Saëns: Caprice andalous, Op. 122',
            'duration': 666.0,
            'artists': ['María Dueñas', 'Mihhail Gerts'],
            'album': 'Saint-Saëns: Caprice andalous, Op. 122',
            'timestamp': 1744977600,
            'upload_date': '20250418',
            'release_timestamp': 1717200000,
            'release_date': '20240601',
        },
        'skip': 'Account Required',
        'params': {'skip_download': 'm3u8'},
    }]

    # TODO: Prune this after livestream and/or album extractors are added
    _GRAPHQL_QUERY = '''
    query videoDetailPage($videoId: ID!, $sliderItemsFirst: Int = 24, $includeSeoFields: Boolean! = false) {
      node(id: $videoId) {
        __typename
        ...contentInfoFields
        ...LiveConcertFields
        ... on LiveConcert {
          booklet {
            pdfUrl
          }
          conductors: artists(role: CONDUCTORS) {
            ...ArtistWithRoleConnectionFields
          }
          curatedContent {
            ...curatedContentContainerFields
          }
          groups {
            id
            name
            typeDisplayName
          }
          isAtmos
          liveConcertType: type
          maxResolution
          metaDescription @include(if: $includeSeoFields)
          metaTitle @include(if: $includeSeoFields)
          performanceWorks {
            ...livePerformanceWorkFields
          }
          shortDescription
          soloists: artists(role: SOLOISTS) {
            ...ArtistWithRoleConnectionFields
          }
          supplementaryText @include(if: $includeSeoFields)
          totalDuration
          vodConcert {
            __typename
            id
          }
        }
        ...VideoFields
        ... on Video {
          conductors: artists(role: CONDUCTORS) {
            ...ArtistWithRoleConnectionFields
          }
          curatedContent {
            ...curatedContentContainerFields
          }
          description
          groups {
            id
            name
            typeDisplayName
          }
          isAtmos
          isLossless
          maxResolution
          metaDescription @include(if: $includeSeoFields)
          metaTitle @include(if: $includeSeoFields)
          productionDate
          soloists: artists(role: SOLOISTS) {
            ...ArtistWithRoleConnectionFields
          }
          supplementaryText @include(if: $includeSeoFields)
          takedownDate
          uploadDate
          videoType: type
        }
        ...VodConcertFields
        ... on VodConcert {
          booklet {
            pdfUrl
          }
          conductors: artists(role: CONDUCTORS) {
            ...ArtistWithRoleConnectionFields
          }
          curatedContent {
            ...curatedContentContainerFields
          }
          groups {
            id
            name
            typeDisplayName
          }
          isAtmos
          metaDescription @include(if: $includeSeoFields)
          metaTitle @include(if: $includeSeoFields)
          maxResolution
          performanceWorks {
            ...PerformanceWorkFields
          }
          productionDate
          shortDescription
          soloists: artists(role: SOLOISTS) {
            ...ArtistWithRoleConnectionFields
          }
          supplementaryText @include(if: $includeSeoFields)
          takedownDate
          uploadDate
          vodConcertType: type
          epochsByRelevance {
            __typename
            id
            title
          }
          genresByRelevance {
            __typename
            id
            title
          }
        }
      }
    }

    fragment contentInfoFields on Node {
      __typename
      ... on Album {
        conductors: artists(role: CONDUCTORS) {
          ...ArtistWithRoleConnectionFields
        }
        soloists: artists(role: SOLOISTS) {
          ...ArtistWithRoleConnectionFields
        }
        atmosUpc
        albumCopyright: copyright
        groups {
          id
          name
          typeDisplayName
        }
        id
        phonographicCopyright
        pictures {
          ...PictureFields
        }
        releaseDate
        title
        totalDuration
        upc
      }
      ... on Track {
        album {
          __typename
          copyright
          phonographicCopyright
          pictures {
            ...PictureFields
          }
          title
        }
        composerDisplayInfo
        conductorDisplayInfo
        duration
        engineerDisplayInfo
        firstReleaseYear
        groupDisplayInfo
        id
        isrc
        recordingSessionEnd
        recordingLocation
        recordingSetting
        producerDisplayInfo
        title
        trackNumber
      }
      ... on LiveConcert {
        conductors: artists(role: CONDUCTORS) {
          ...ArtistWithRoleConnectionFields
        }
        soloists: artists(role: SOLOISTS) {
          ...ArtistWithRoleConnectionFields
        }
        copyright
        endTime
        groups {
          id
          name
          typeDisplayName
        }
        finalEndTime
        id
        isrc
        longFormConcertIntroduction
        partners {
          name
          type
        }
        photographer
        pictures {
          ...PictureFields
        }
        production
        reruns {
          ...liveConcertRerunFields
        }
        startTime
        streamStartTime
        streamVariants {
          ...streamVariantFields
        }
        subtitle
        title
        totalDuration
        type
        typeDisplayName
        videoDirector
      }
      ... on Video {
        conductors: artists(role: CONDUCTORS) {
          ...ArtistWithRoleConnectionFields
        }
        soloists: artists(role: SOLOISTS) {
          ...ArtistWithRoleConnectionFields
        }
        copyright
        duration
        groups {
          id
          name
          typeDisplayName
        }
        id
        isrc
        photographer
        pictures {
          ...PictureFields
        }
        production
        productionDate
        subtitle
        takedownDate
        title
        typeDisplayName
        videoDirector
      }
      ... on VodConcert {
        conductors: artists(role: CONDUCTORS) {
          ...ArtistWithRoleConnectionFields
        }
        soloists: artists(role: SOLOISTS) {
          ...ArtistWithRoleConnectionFields
        }
        copyright
        courtesyOf
        groups {
          id
          name
          typeDisplayName
        }
        id
        isrc
        partners {
          name
          type
        }
        photographer
        pictures {
          ...PictureFields
        }
        production
        productionDate
        longFormConcertIntroduction
        subtitle
        takedownDate
        title
        totalDuration
        typeDisplayName
        videoDirector
      }
    }

    fragment ArtistWithRoleConnectionFields on ArtistWithRoleConnection {
      edges {
        role {
          displayName
        }
        node {
          id
          name
        }
      }
    }

    fragment PictureFields on Picture {
      id
      url
      type
    }

    fragment liveConcertRerunFields on LiveConcertRerun {
      id
      streamStartTime
      endTime
      startTime
    }

    fragment streamVariantFields on StreamVariant {
      manifestType
      publicationLevel
      streamType
      url
    }

    fragment LiveConcertFields on LiveConcert {
      endTime
      finalEndTime
      geoAccessCountries
      geoAccessMode
      id
      pictures {
        ...PictureFields
      }
      plannedForVod
      publicationLevel
      reruns {
        ...liveConcertRerunFields
      }
      startTime
      streamVariants {
        ...streamVariantFields
      }
      streamStartTime
      subtitle
      title
      trailerStreamVariants {
        ...streamVariantFields
      }
      type
      typeDisplayName
    }

    fragment curatedContentContainerFields on CuratedContentContainerV2 {
      __typename
      ...ListSliderFields
      ...BannerFields
    }

    fragment ListSliderFields on ListSlider {
      id
      headline
      layout
      items(first: $sliderItemsFirst) {
        __typename
        ...AlbumFields
        ...ArtistFields
        ...EpochFields
        ...GenreFields
        ...GroupFields
        ...LiveConcertTeaserFields
        ...PartnerFields
        ...VideoTeaserFields
        ...VodConcertTeaserFields
        ...favoritesFields
        ...playbackProgressFields
        ...workFields
        ...curatedContentLinkFields
        ...articleFields
        ...EditorialPlaylistFields
        ...playbackFields
        ...focusCardFields
      }
    }

    fragment AlbumFields on Album {
      artistAndGroupDisplayInfo
      id
      pictures {
        ...PictureFields
      }
      title
    }

    fragment ArtistFields on Artist {
      id
      name
      roles {
        ...RoleFields
      }
      pictures {
        ...PictureFields
      }
    }

    fragment RoleFields on Role {
      __typename
      id
      type
      displayName
    }

    fragment EpochFields on Epoch {
      id
      endYear
      pictures {
        ...PictureFields
      }
      startYear
      title
    }

    fragment GenreFields on Genre {
      id
      pictures {
        ...PictureFields
      }
      title
    }

    fragment GroupFields on Group {
      id
      name
      typeDisplayName
      pictures {
        ...PictureFields
      }
    }

    fragment LiveConcertTeaserFields on LiveConcert {
      endTime
      finalEndTime
      geoAccessCountries
      geoAccessMode
      id
      pictures {
        ...PictureFields
      }
      plannedForVod
      publicationLevel
      reruns {
        ...liveConcertRerunFields
      }
      startTime
      streamStartTime
      subtitle
      title
      type
      typeDisplayName
    }

    fragment PartnerFields on Partner {
      id
      name
      typeDisplayName
      subtypeDisplayName
      pictures {
        ...PictureFields
      }
    }

    fragment VideoTeaserFields on Video {
      id
      archiveReleaseDate
      title
      subtitle
      pictures {
        ...PictureFields
      }
      duration
      typeDisplayName
      geoAccessCountries
      geoAccessMode
      publicationLevel
      takedownDate
    }

    fragment VodConcertTeaserFields on VodConcert {
      id
      archiveReleaseDate
      pictures {
        ...PictureFields
      }
      subtitle
      title
      typeDisplayName
      totalDuration
      geoAccessCountries
      geoAccessMode
      publicationLevel
      takedownDate
    }

    fragment favoritesFields on Favorite {
      id
      __typename
      content {
        __typename
        ... on Album {
          ...AlbumFields
        }
        ... on PerformanceWork {
          ...performanceWorkConcertFields
        }
        ... on Video {
          ...VideoTeaserFields
        }
        ... on EditorialPlaylist {
          ...EditorialPlaylistFields
        }
      }
    }

    fragment performanceWorkConcertFields on PerformanceWork {
      id
      vodConcert {
        __typename
        id
        pictures {
          ...PictureFields
        }
        title
        totalDuration
        typeDisplayName
        publicationLevel
      }
      duration
      work {
        title
      }
    }

    fragment EditorialPlaylistFields on EditorialPlaylist {
      __typename
      id
      title
      playlistDescription: description
      totalDuration
      totalItems
      typeDisplayName
      pictures {
        ...PictureFields
      }
    }

    fragment playbackProgressFields on PlaybackProgress {
      __typename
      id
    }

    fragment workFields on Work {
      __typename
      id
      title
      composers {
        __typename
        id
        name
      }
    }

    fragment curatedContentLinkFields on CuratedContentLink {
      id
      slugV2
      title
      pictures {
        ...PictureFields
      }
    }

    fragment articleFields on Article {
      __typename
      date
      headline
      id
      pictures {
        ...PictureFields
      }
      teaserHeadline
    }

    fragment playbackFields on Playback {
      __typename
      id
      content {
        __typename
        ... on PerformanceWork {
          ...performanceWorkConcertFields
        }
        ... on Track {
          ...playbackTrackFields
          album {
            __typename
            ...AlbumFields
          }
        }
        ... on Video {
          ...VideoTeaserFields
        }
      }
      container {
        __typename
        ... on Album {
          id
          title
        }
        ... on EditorialPlaylist {
          id
          title
        }
        ... on VodConcert {
          id
          title
        }
      }
    }

    fragment playbackTrackFields on Track {
      ...trackListFields
      artistAndGroupDisplayInfo
      streamVariants {
        ...streamVariantFields
      }
    }

    fragment trackListFields on Track {
      __typename
      id
      composerDisplayInfo
      duration
      title
      trackNumber
      album {
        id
      }
    }

    fragment focusCardFields on FocusCard {
      __typename
      body
      headline
      id
      link {
        id
        type
        pageType
        slug
      }
      pictures {
        ...PictureFields
      }
    }

    fragment BannerFields on Banner {
      description
      link
      pictures {
        ...PictureFields
      }
      title
    }

    fragment livePerformanceWorkFields on LivePerformanceWork {
      __typename
      id
      soloists: artists(role: SOLOISTS) {
        ...ArtistWithRoleConnectionFields
      }
      groups {
        edges {
          node {
            id
            name
            typeDisplayName
          }
        }
      }
      work {
        ...workFields
      }
    }

    fragment VideoFields on Video {
      id
      archiveReleaseDate
      title
      subtitle
      pictures {
        ...PictureFields
      }
      streamVariants {
        ...streamVariantFields
      }
      trailerStreamVariants {
        ...streamVariantFields
      }
      duration
      typeDisplayName
      geoAccessCountries
      geoAccessMode
      publicationLevel
      takedownDate
    }

    fragment VodConcertFields on VodConcert {
      id
      archiveReleaseDate
      pictures {
        ...PictureFields
      }
      subtitle
      title
      typeDisplayName
      totalDuration
      geoAccessCountries
      geoAccessMode
      trailerStreamVariants {
        ...streamVariantFields
      }
      publicationLevel
      takedownDate
    }

    fragment PerformanceWorkFields on PerformanceWork {
      __typename
      id
      soloists: artists(role: SOLOISTS) {
        ...ArtistWithRoleConnectionFields
      }
      groups {
        edges {
          node {
            id
            name
            typeDisplayName
          }
        }
      }
      work {
        ...workFields
      }
      streamVariants {
        ...streamVariantFields
      }
      vodConcert {
        __typename
        id
      }
      duration
      cuePoints {
        mark
        title
      }
    }
  '''

    _ACCESS_TOKEN = None
    _REFRESH_TOKEN = None
    _CACHE_KEY = 'stageplus_data'

    def _refresh_token(self, rf_token):
        if not rf_token:
            return None
        try:
            refresh_data = self._call_login_api({
                'grant_type': 'refresh_token',
                'refresh_token': rf_token,
            }, note='Refreshing access token')
        except ExtractorError:
            self.cache.store(self._NETRC_MACHINE, self._CACHE_KEY, [None, None])
            self._perform_login(*self._get_login_info())
        self._parse_login_data(refresh_data)

    def _call_login_api(self, payload, **kwargs):
        return self._download_json(
            'https://audience.api.stageplus.io/oauth/token', None,
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://www.stage-plus.com',
            },
            data=json.dumps({
                'device_info': 'Chrome (Linux)',
                'client_device_id': str(uuid.uuid4()),
                **payload,
            }, separators=(',', ':')).encode(),
            **kwargs,
        )

    def _parse_login_data(self, data, error_note=None):
        self._ACCESS_TOKEN = data.get('access_token')
        self._REFRESH_TOKEN = data.get('refresh_token')
        if not self._ACCESS_TOKEN:
            raise ExtractorError(f'{error_note or "login failed"}; unable to get access token')
        self.cache.store(self._NETRC_MACHINE, self._CACHE_KEY, [
            self._ACCESS_TOKEN,
            self._REFRESH_TOKEN,
        ])

    def _perform_login(self, username, password):
        auth = self._call_login_api({
            'grant_type': 'password',
            'username': username,
            'password': password,
        }, note='Logging in', expected_status=400)
        if auth.get('code') == 'INVALID_CREDENTIALS':
            raise ExtractorError('Invalid Username/Password', expected=True)
        elif msg := auth.get('message'):
            raise ExtractorError(f'Login failed; api says: {msg}')
        self._parse_login_data(auth)

    def _real_initialize(self):
        if self._ACCESS_TOKEN:
            return

        self._ACCESS_TOKEN = try_call(
            lambda: self._get_cookies('https://www.stage-plus.com/')['dgplus_access_token'].value)
        if not self._ACCESS_TOKEN:
            self.raise_login_required()

    def _parse_metadata(self, data, common_metadata, track_idx=None):
        return filter_dict({
            'id': data['id'],
            'album': data.get('title'),
            'album_artists': common_metadata.get('artist'),
            'track_number': track_idx,
            **common_metadata,
            **filter_dict(traverse_obj(data, {
                'title': ('work', 'title'),
                'track': ('work', 'title'),
                'duration': ('duration', {float_or_none}),
                'chapters': (
                    'cuePoints', lambda _, v: float_or_none(v['mark']) is not None, {
                        'title': 'title',
                        'start_time': ('mark', {float_or_none}),
                    }),
                'artists': ('artists', 'edges', ..., 'node', 'name'),
                'composers': (('work', None), 'composers', ..., 'name'),
                'genre': ('work', 'genre', 'title'),
            })),
        })

    def _extract_formats_and_subs(self, data, concert_id):
        if not data.get('streamVariants'):
            return {}
        formats = []
        subtitles = {}
        for fmt_url in traverse_obj(data, ('streamVariants', ..., 'url', {url_or_none}), default=[]):
            try:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(fmt_url, concert_id, 'mp4', m3u8_id='hls', query={'token': self._ACCESS_TOKEN})
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    self.raise_no_formats('Subscription Required', expected=True)
                raise
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        return {
            'formats': formats,
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        concert_id = self._match_id(url)

        data = self._download_json('https://audience.api.stageplus.io/graphql', concert_id, headers={
            'authorization': f'Bearer {self._ACCESS_TOKEN}',
            'content-type': 'application/json',
            'Origin': 'https://www.stage-plus.com',
        }, data=json.dumps({
            'query': self._GRAPHQL_QUERY,
            'variables': {'videoId': concert_id},
            'operationName': 'videoDetailPage',
        }, separators=(',', ':')).encode())['data']['node']

        metadata = traverse_obj(data, {
            'title': 'title',
            'description': ('shortDescription', {str}),
            'artists': ('curatedContent',
                        lambda _, x: x['headline'] == 'Artists', 'items', lambda _, x: x['__typename'] == 'Artist', 'name', {str}),
            'timestamp': ('archiveReleaseDate', {unified_timestamp}),
            'release_timestamp': ('productionDate', {unified_timestamp}),
        })

        thumbnails = traverse_obj(data, ('pictures', lambda _, v: url_or_none(v['url']), {
            'id': 'name',
            'url': 'url',
        })) or None

        entries = []
        for idx, video in enumerate(traverse_obj(data, (
                'performanceWorks', lambda _, v: v['id'] and url_or_none(v['streamVariants'][0]['url']))), 1):
            fmts_and_subs = self._extract_formats_and_subs(video, concert_id)
            if not fmts_and_subs:
                continue
            entries.append({
                **self._parse_metadata(video, metadata, idx),
                **fmts_and_subs,
            })

        if not (entries or data.get('performanceWorks')):
            fmts_and_subs = self._extract_formats_and_subs(data, concert_id)
            if fmts_and_subs:
                return {
                    **self._parse_metadata(data, metadata),
                    **metadata,
                    **fmts_and_subs,
                }

        return self.playlist_result(entries, concert_id, thumbnails=thumbnails, **metadata)
