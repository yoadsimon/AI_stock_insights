import os

from moviepy.editor import (
    AudioFileClip,
    VideoFileClip,
    TextClip,
    concatenate_videoclips,
    CompositeVideoClip,
)
import ffmpeg

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
        if sentence.get("is_last_sentence") is True:
            clip_duration += 0.5
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
                fontsize=160,
                color='white',
                stroke_color='black',
                stroke_width=6,
                font='Arial-Bold',
                method='caption'
            ).set_start(start_time_in_seconds).set_duration(duration).set_position('center')
            clips.append(text_clip)
    return clips


def add_disclaimer(video, disclaimer_video_path):
    print("Adding disclaimer video...")
    if os.path.exists(disclaimer_video_path):
        disclaimer_clip = VideoFileClip(disclaimer_video_path)
        final_video = concatenate_videoclips([video, disclaimer_clip], method="compose")
        return final_video, disclaimer_clip
    else:
        print("Disclaimer video not found. Proceeding without it.")
        return video, None


def create_youtube_shorts_video(full_video_path, shorts_video_path, disclaimer_video_path):
    try:
        import ffmpeg
    except ImportError:
        print("Please install the 'ffmpeg' package to create YouTube Shorts videos.")
        shorts_video_path = None
        return None
    probe = ffmpeg.probe(full_video_path)
    duration = float(probe['format']['duration'])
    trimmed_duration = duration - 7
    if trimmed_duration <= 0:
        trimmed_duration = duration
    trimmed_duration *= 0.8
    print(f"Creating YouTube Shorts video of duration {trimmed_duration:.2f} seconds...")
    SHORTS_DESIRED_WIDTH, SHORTS_DESIRED_HEIGHT = 1080, 1920

    def process_input(video_input):
        # Scale the original video to fit the width, maintaining aspect ratio
        scaled_video = video_input.video.filter('scale', SHORTS_DESIRED_WIDTH, -1)
        # Create a blurred background by scaling and blurring the original video
        blurred_bg = (
            video_input.video
            .filter('scale', SHORTS_DESIRED_WIDTH, SHORTS_DESIRED_HEIGHT)
            .filter('boxblur', luma_radius=10, luma_power=1)
        )
        # Overlay the scaled video onto the blurred background, centered vertically
        overlaid = ffmpeg.overlay(blurred_bg, scaled_video, x=0, y='(H-h)/2')
        return overlaid

    if os.path.exists(disclaimer_video_path):
        print("Disclaimer video found, processing with disclaimer.")
        in1 = ffmpeg.input(full_video_path, ss=0, t=trimmed_duration)
        in2 = ffmpeg.input(disclaimer_video_path)
        v1 = process_input(in1)
        v2 = process_input(in2)
        a1 = in1.audio
        a2 = in2.audio
        v_concat = ffmpeg.concat(v1, v2, v=1, a=0).node
        a_concat = ffmpeg.concat(a1, a2, v=0, a=1).node
        out = ffmpeg.output(
            v_concat[0], a_concat[0], shorts_video_path,
            vcodec='libx264', acodec='aac', strict='experimental'
        ).global_args('-loglevel', 'error').overwrite_output()
        out.run()
    else:
        print("Disclaimer video not found. Proceeding without it.")
        in1 = ffmpeg.input(full_video_path, ss=0, t=trimmed_duration)
        v1 = process_input(in1)
        a1 = in1.audio
        out = ffmpeg.output(
            v1, a1, shorts_video_path,
            vcodec='libx264', acodec='aac', strict='experimental'
        ).global_args('-loglevel', 'error').overwrite_output()
        out.run()
    print(f"YouTube Shorts video created at {shorts_video_path}")


def create_video(
        audio_path,
        video_path,
        sentences_list_with_timings,
        background_videos,
        disclaimer_video_path,
        youtube_shorts_video_path,
):
    audio = load_audio(audio_path)
    background_clip, bg_video_clips = load_background_clips(
        background_videos, audio.duration, sentences_list_with_timings
    )
    text_clips = generate_text_clips(sentences_list_with_timings)
    if background_clip:
        main_video = CompositeVideoClip([background_clip] + text_clips)
    else:
        main_video = CompositeVideoClip(text_clips)
    main_video = main_video.set_audio(audio)
    final_main_video, disclaimer_clip = add_disclaimer(main_video, disclaimer_video_path)
    print("Writing main video...")
    final_main_video.write_videofile(video_path, fps=24, audio_codec="aac")
    if disclaimer_clip:
        disclaimer_clip.close()

    final_main_video.close()
    main_video.close()
    audio.close()
    if background_clip:
        background_clip.close()
    for clip in text_clips:
        clip.close()
    for bg_clip in bg_video_clips:
        bg_clip.close()

    create_youtube_shorts_video(video_path, youtube_shorts_video_path, disclaimer_video_path)
