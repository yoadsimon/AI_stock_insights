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
        # Retrieve credentials from Airflow connection
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
        logger.info(f"Video uploaded successfully: https://www.youtube.com/watch?v={response['id']}")
    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        sys.exit(1)


def upload_video_youtube(video_file_path, title, description, keywords='', category='22', privacyStatus='public'):
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
    initialize_upload(youtube, options)
