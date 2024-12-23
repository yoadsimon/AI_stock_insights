import os
import sys
import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def authenticate_youtube(conn_id='youtube_api'):
    try:
        print("Authenticating with YouTube API...")
        if os.environ.get("LOCAL"):
            client_id = os.getenv('client_id')
            client_secret = os.getenv('client_secret')
            refresh_token = os.getenv('refresh_token')
            access_token = os.getenv('access_token')
            token_uri = os.getenv('token_uri', "https://oauth2.googleapis.com/token")
        else:
            from airflow.hooks.base_hook import BaseHook
            conn = BaseHook.get_connection(conn_id)
            extra = conn.extra_dejson
            client_id = extra.get('client_id')
            client_secret = extra.get('client_secret')
            refresh_token = extra.get('refresh_token')
            access_token = extra.get('access_token')
            token_uri = extra.get('token_uri', "https://oauth2.googleapis.com/token")

        if not client_id or not client_secret or not refresh_token:
            logger.error('Missing YouTube API credentials.')
            sys.exit(1)

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            token_uri=token_uri,
            client_secret=client_secret,
            scopes=SCOPES
        )

        # Refresh the token if necessary
        if creds.expired or not creds.valid:
            creds.refresh(Request())

        return creds
    except Exception as e:
        logger.error(f"Failed to authenticate with YouTube API: {e}")
        sys.exit(1)


def initialize_upload(youtube, options, is_short=False):
    print("Uploading video to YouTube...")
    tags = options['keywords'].split(',') if options['keywords'] else None
    body = {
        'snippet': {
            'title': options['title'],
            'description': options['description'],
            'tags': tags,
            'categoryId': options['category']
        },
        'status': {
            'privacyStatus': options['privacyStatus']
        }
    }
    if is_short:
        body['videoType'] = 'SHORT'
    try:
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(options['file'], chunksize=-1, resumable=True)
        )
        response = insert_request.execute()
        link = f"https://www.youtube.com/watch?v={response['id']}"
        print(f"Video uploaded successfully: {link}")
        return link
    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        sys.exit(1)


def upload_youtube_shorts(youtube, options, youtube_shorts_video_path, full_video_link):
    shorts_options = options.copy()
    shorts_options['file'] = youtube_shorts_video_path

    shorts_options['title'] = f"{options['title']} #shorts"
    shorts_options['description'] = (f"This is only a part from the real video - watch the full video here:\n"
                                     f"{full_video_link}\n\n#shorts")
    shorts_options['keywords'] = options.get('keywords', '') + ',shorts'

    shorts_video_link = initialize_upload(youtube, shorts_options, is_short=True)
    return shorts_video_link


def upload_video_youtube(video_file_path,
                         title,
                         description,
                         youtube_shorts_video_path=None,
                         keywords='',
                         category='22',
                         is_mock=False
                         ):
    privacyStatus = 'public' if not is_mock else 'private'
    video_file_path = os.path.abspath(video_file_path)

    creds = authenticate_youtube()
    youtube = build('youtube', 'v3', credentials=creds)
    options = {
        'file': video_file_path,
        'title': title,
        'description': description,
        'category': category,
        'keywords': keywords,
        'privacyStatus': privacyStatus
    }
    full_video_link = initialize_upload(youtube, options)
    if youtube_shorts_video_path and os.path.exists(youtube_shorts_video_path):
        upload_youtube_shorts(youtube, options, youtube_shorts_video_path, full_video_link)
