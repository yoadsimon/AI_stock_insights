import os
import sys
import logging
from airflow.hooks.base import BaseHook
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def authenticate_youtube(conn_id='youtube_api'):
    try:
        print("Authenticating with YouTube API...")
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


def initialize_upload(youtube, options):
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

    # Modify title and description to include #shorts and link to the full video
    shorts_options['title'] = f"{options['title']} #shorts"
    shorts_options['description'] = f"{options['description']}\n\nWatch the full video here: {full_video_link}\n\n#shorts"

    # Add 'shorts' to keywords to increase visibility
    shorts_options['keywords'] = options.get('keywords', '') + ',shorts'

    # Upload the Shorts video using the existing initialize_upload function
    shorts_video_link = initialize_upload(youtube, shorts_options)
    return shorts_video_link


def upload_video_youtube(video_file_path,
                         title,
                         description,
                         youtube_shorts_video_path,
                         keywords='',
                         category='22',
                         privacyStatus='public'
                         ):
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
    upload_youtube_shorts(youtube, options, youtube_shorts_video_path, full_video_link)
