import datetime
import time
from common.audio_synthesis import text_to_audio
from common.create_content import create_content
from common.upload_to_youtube import upload_video_youtube
from common.utils.consts import MARKET_TIME_ZONE
from common.utils.open_ai import create_description_youtube_video, match_text_to_video
import glob
import logging
import os
from pydub import AudioSegment

from common.video_creation import create_video


def execute_daily_stock_analysis(stock_symbol='NVDA', company_name='NVIDIA Corporation', is_mock=False):
    logging.info("Starting the script.")

    now = datetime.datetime.now(MARKET_TIME_ZONE)
    if is_mock:
        use_temp_file = False
        mock_data_input_now = now.replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        use_temp_file = False
        mock_data_input_now = None

    text = create_content(use_temp_file=use_temp_file,
                          mock_data_input_now=mock_data_input_now,
                          stock_symbol=stock_symbol,
                          company_name=company_name)

    title_youtube = f"{company_name} - {stock_symbol} AI Stock Analysis - {now.strftime('%Y-%m-%d')}"
    description_youtube = create_description_youtube_video(text=text, company_name=company_name,
                                                           stock_symbol=stock_symbol, now=now)
    # text = "This is a test, this is only a test. If this were a real emergency, you would be instructed to do something else."
    #
    # title_youtube = "This is a test"
    # description_youtube = "This is a test"

    text = text.replace("*", "").replace('"', "'")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    audio_path = os.path.join(script_dir, "results/output_audio.mp3")
    video_path = os.path.join(script_dir, "results/output_video.mp4")

    logging.info("Converting text to audio...")
    start_time = time.time()
    sentences_list_with_timings = text_to_audio(text, audio_path)
    logging.info(f"Text to audio conversion completed in {time.time() - start_time:.2f} seconds.")

    for sentence in sentences_list_with_timings:
        sentence['video_name'] = match_text_to_video(sentence['sentence'])
    print(f"sentences_list_with_timings : {sentences_list_with_timings}")
    background_videos_dir = os.path.join(script_dir, "inputs")
    background_videos = glob.glob(os.path.join(background_videos_dir, "*.mp4")) or None

    audio = AudioSegment.from_file(audio_path)
    logging.info(f"Generated audio duration: {audio.duration_seconds} seconds")

    logging.info("Creating video with text...")
    start_time = time.time()
    create_video(
        audio_path=audio_path,
        video_path=video_path,
        sentences_list_with_timings=sentences_list_with_timings,
        background_videos=background_videos
    )
    logging.info(f"Video creation completed in {time.time() - start_time:.2f} seconds.")
    logging.info("Uploading video to YouTube...")
    upload_video_youtube(
        video_file_path=video_path,
        title=title_youtube,
        description=description_youtube,
        keywords='finance,stock market,AI',
        category='22',
        privacyStatus='public'
    )

    logging.info("Script finished successfully.")

# if __name__ == "__main__":
#     main()
