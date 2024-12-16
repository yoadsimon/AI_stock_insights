import os

from moviepy.editor import AudioFileClip, VideoFileClip, TextClip, concatenate_videoclips, CompositeVideoClip


def load_audio(audio_path):
    return AudioFileClip(audio_path)


def load_background_clips(background_videos, total_audio_duration, sentences_list_with_timings):
    if background_videos is None:
        return None, []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_dir = os.path.join(script_dir, 'inputs')

    background_clips = []
    bg_videos = []
    current_duration = 0
    print("now going to loop through sentences_list_with_timings")
    for sentence in sentences_list_with_timings:
        video_name = sentence['video_name']
        print(f"video_name: {video_name}")
        if current_duration >= total_audio_duration:
            break
        file_name = os.path.join(inputs_dir, video_name)
        print(f"file_name: {file_name}")
        try:
            bg_video = VideoFileClip(file_name)
            bg_videos.append(bg_video)
            print(f"added {file_name}")
        except Exception as e:
            print(f"Error loading video '{file_name}': {e}")
            continue
        clip_duration = (sentence['end'] - sentence['start']) / 1000
        video_duration = bg_video.duration
        clip_duration = min(clip_duration, video_duration)
        if clip_duration <= 0:
            continue
        bg_clip = bg_video.subclip(0, clip_duration).resize((640, 480))
        background_clips.append(bg_clip)
        current_duration += clip_duration

    while current_duration < total_audio_duration:
        video_name = "Interactive_Trading_Screen.mp4"
        file_name = os.path.join(inputs_dir, video_name)
        print(f"file_name: {file_name}")
        try:
            bg_video = VideoFileClip(file_name)
            bg_videos.append(bg_video)
            print(f"added {file_name}")
        except Exception as e:
            print(f"Error loading video '{file_name}': {e}")
            break
        clip_duration = min(bg_video.duration, total_audio_duration - current_duration)
        bg_clip = bg_video.subclip(0, clip_duration).resize((640, 480))
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
    for sentence in sentences_list_with_timings:
        for timing in sentence['words_in_sentence']:
            word = timing['word']
            start_time_in_seconds = timing['start'] / 1000
            duration = (timing['end'] - timing['start']) / 1000
            text_clip = TextClip(word, fontsize=70, color='white', size=(640, 480), method='caption', font='Arial')
            text_clip = text_clip.set_start(start_time_in_seconds).set_duration(duration).set_pos('center')
            clips.append(text_clip)
    return clips


def create_video(audio_path, video_path, sentences_list_with_timings, background_videos):
    audio = load_audio(audio_path)
    total_audio_duration = audio.duration
    background, bg_videos = load_background_clips(background_videos, total_audio_duration, sentences_list_with_timings)
    print(f"got {len(bg_videos)} background videos")
    clips = generate_text_clips(sentences_list_with_timings)
    video = CompositeVideoClip([background] + clips) if background else CompositeVideoClip(clips)
    video = video.set_audio(audio)
    video.write_videofile(video_path, fps=24, audio_codec='aac')
    video.close()
    audio.close()
    for bg_video in bg_videos:
        bg_video.close()
