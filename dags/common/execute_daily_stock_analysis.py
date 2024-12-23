import datetime
from common.audio_synthesis import text_to_audio
from common.create_content import create_content
from common.upload_to_youtube import upload_video_youtube
from common.utils.consts import MARKET_TIME_ZONE
from common.utils.open_ai import create_description_youtube_video, match_text_to_video
import glob
import os

from common.utils.stock_market_time import StockMarketTime
from common.utils.utils import clean_dir
from common.video_creation import create_video
from tqdm import tqdm


def execute_daily_stock_analysis(stock_symbol='NVDA', company_name='NVIDIA Corporation', is_mock=False):
    now = datetime.datetime.now(MARKET_TIME_ZONE)
    if is_mock:
        use_temp_file = True  # change to False for testing all the way through
        mock_data_input_now = now.replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        use_temp_file = False
        mock_data_input_now = None
    stock_market_time = StockMarketTime(mock_data_input_now)

    if not is_mock and not stock_market_time.is_next_time_open_today:
        print("Market Won't Open Today, Exiting...")
        return

    print(f"Creating content...")
    text = create_content(use_temp_file=use_temp_file,
                          stock_symbol=stock_symbol,
                          company_name=company_name,
                          stock_market_time=stock_market_time)
    title_youtube = f"{company_name} - {stock_symbol} AI Stock Analysis - {now.strftime('%Y-%m-%d')}"
    description_youtube = create_description_youtube_video(text=text, company_name=company_name,
                                                           stock_symbol=stock_symbol, now=now)

    print(f"title_youtube:\n{title_youtube}")
    print(f"description_youtube:\n{description_youtube}")
    text = text.replace("*", "").replace('"', "'")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(script_dir, "results/output_audio.mp3")
    video_path = os.path.join(script_dir, "results/output_video.mp4")
    youtube_shorts_video_path = os.path.join(script_dir, "results/youtube_shorts_output_video.mp4")
    disclaimer_video_path = os.path.join(script_dir, "results/disclaimer_video.mp4")

    print("Converting text to audio...")
    sentences_list_with_timings = text_to_audio(text, audio_path)

    print(f"Matching text to video...")
    last_video_name = None
    for sentence in tqdm(sentences_list_with_timings):
        sentence['video_name'] = match_text_to_video(sentence['sentence'], last_video_name)
        last_video_name = sentence['video_name']
        print(f"last_video_name: {last_video_name}")

    background_videos_dir = os.path.join(script_dir, "inputs")
    background_videos = glob.glob(os.path.join(background_videos_dir, "*.mp4")) or None

    print("Creating video with text...")
    create_video(
        audio_path=audio_path,
        video_path=video_path,
        sentences_list_with_timings=sentences_list_with_timings,
        background_videos=background_videos,
        disclaimer_video_path=disclaimer_video_path,
        youtube_shorts_video_path=youtube_shorts_video_path
    )

    print("Uploading video to YouTube...")
    upload_video_youtube(
        video_file_path=video_path,
        title=title_youtube,
        description=description_youtube,
        youtube_shorts_video_path=youtube_shorts_video_path,
        keywords='finance,stock market,AI',
        category='22',
        is_mock=is_mock
    )

    print("Cleaning up...")
    dir_name = os.path.join(script_dir, "results")
    clean_dir(dir_name=dir_name)

    print("Script finished successfully.")

# if __name__ == "__main__":
#     main()
