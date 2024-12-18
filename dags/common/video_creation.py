import os

from moviepy.editor import AudioFileClip, VideoFileClip, TextClip, concatenate_videoclips, CompositeVideoClip

DESIRED_WIDTH, DESIRED_HEIGHT = 1920, 1080


def load_audio(audio_path):
    return AudioFileClip(audio_path)


def resize_video(bg_video, clip_duration, video_name):
    bg_clip = bg_video.subclip(0, clip_duration)
    desired_width, desired_height = DESIRED_WIDTH, DESIRED_HEIGHT
    try:
        bg_clip = bg_clip.resize(width=desired_width)
        if bg_clip.h > desired_height:
            y_center = bg_clip.h / 2
            x_center = bg_clip.w / 2
            bg_clip = bg_clip.crop(width=desired_width, height=desired_height,
                                   x_center=x_center, y_center=y_center)
    except Exception as e:
        raise Exception(f"Error resizing video '{video_name}': {e}")
    return bg_clip


def load_background_clips(background_videos, total_audio_duration, sentences_list_with_timings):
    if background_videos is None:
        return None, []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_dir = os.path.join(script_dir, 'inputs')

    background_clips = []
    bg_videos = []
    current_duration = 0

    print(f"Creating background clips...")
    for sentence in sentences_list_with_timings:
        video_name = sentence['video_name']
        if current_duration >= total_audio_duration:
            break
        file_name = os.path.join(inputs_dir, video_name)
        try:
            bg_video = VideoFileClip(file_name)
            bg_videos.append(bg_video)
        except Exception as e:
            print(f"Error loading video '{file_name}': {e}")
            continue
        clip_duration = (sentence['end'] - sentence['start']) / 1000
        video_duration = bg_video.duration
        clip_duration = min(clip_duration, video_duration)
        if clip_duration <= 0:
            continue
        # bg_clip = bg_video.subclip(0, clip_duration).resize((640, 480))
        bg_clip = resize_video(bg_video, clip_duration, video_name)
        background_clips.append(bg_clip)
        current_duration += clip_duration

    while current_duration < total_audio_duration:
        video_name = "Interactive_Trading_Screen.mp4"
        file_name = os.path.join(inputs_dir, video_name)
        try:
            bg_video = VideoFileClip(file_name)
            bg_videos.append(bg_video)
        except Exception as e:
            print(f"Error loading video '{file_name}': {e}")
            break
        clip_duration = min(bg_video.duration, total_audio_duration - current_duration)
        bg_clip = resize_video(bg_video, clip_duration, video_name)
        background_clips.append(bg_clip)
        current_duration += clip_duration

    if background_clips:
        try:
            concatenated_background = concatenate_videoclips(background_clips)
            return concatenated_background, bg_videos
        except Exception as e:
            print(f"Error concatenating video clips: {e}")
            return None, bg_videos
    else:
        return None, bg_videos


def generate_text_clips(sentences_list_with_timings):
    clips = []
    print("Generating background text clips...")
    for sentence in sentences_list_with_timings:
        for timing in sentence['words_in_sentence']:
            word = timing['word']
            start_time_in_seconds = timing['start'] / 1000.0
            duration = (timing['end'] - timing['start']) / 1000.0

            text_clip = TextClip(
                word,
                fontsize=140,
                color='white',
                stroke_color='black',
                stroke_width=3,
                font='Arial-Bold',
                size=(DESIRED_WIDTH, DESIRED_HEIGHT),
                method='caption'
            ).set_start(start_time_in_seconds).set_duration(duration).set_pos('center')

            clips.append(text_clip)
    return clips


def create_video(audio_path, video_path, sentences_list_with_timings, background_videos):
    audio = load_audio(audio_path)
    total_audio_duration = audio.duration
    background, bg_videos = load_background_clips(background_videos, total_audio_duration, sentences_list_with_timings)
    clips = generate_text_clips(sentences_list_with_timings)
    video = CompositeVideoClip([background] + clips) if background else CompositeVideoClip(clips)
    print("Writing video...")
    video = video.set_audio(audio)
    video.write_videofile(video_path, fps=24, audio_codec='aac')
    video.close()
    audio.close()
    for bg_video in bg_videos:
        bg_video.close()
