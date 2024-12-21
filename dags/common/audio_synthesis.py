import os

import boto3
import json
from pydub import AudioSegment
from airflow.hooks.base_hook import BaseHook


def text_to_audio(
        text,
        audio_path="common/results/output_audio.mp3",
        conn_id='aws_default'
):
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson or {}
    aws_access_key_id = conn.login
    aws_secret_access_key = conn.password
    region_name = extra.get('region_name', 'us-east-1')

    polly_client = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    ).client('polly')

    print(f"AWS Connection was successful...")

    response_audio = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Gregory',
        Engine='neural'
    )

    if "AudioStream" in response_audio:
        audio_path = os.path.abspath(audio_path)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, 'wb') as file:
            file.write(response_audio['AudioStream'].read())
    else:
        raise Exception("Could not stream audio")

    audio_segment = AudioSegment.from_mp3(audio_path)
    audio_duration_ms = len(audio_segment)

    response_marks = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='json',
        SpeechMarkTypes=['word', 'sentence'],
        VoiceId='Gregory',
        Engine='neural'
    )

    print(f"Preparing speech marks...")
    if 'AudioStream' in response_marks:
        speech_marks_data = response_marks['AudioStream'].read().decode('utf-8').split('\n')
        speech_marks = [json.loads(mark) for mark in speech_marks_data if mark.strip()]

        list_of_sentences = []
        current_sentence = None
        current_words_in_sentence = []

        for mark in speech_marks:
            if mark['type'] == 'sentence':
                if current_sentence is not None:
                    current_sentence['end'] = mark['time']
                    if current_words_in_sentence:
                        current_words_in_sentence[-1]['end'] = mark['time']
                    current_sentence['words_in_sentence'] = current_words_in_sentence
                    list_of_sentences.append(current_sentence)
                current_sentence = {
                    "sentence": mark['value'],
                    "start": mark['time'],
                }
                current_words_in_sentence = []
            elif mark['type'] == 'word':
                word_dict = {
                    "word": mark['value'],
                    "start": mark['time'],
                }
                if current_words_in_sentence:
                    current_words_in_sentence[-1]['end'] = mark['time']
                current_words_in_sentence.append(word_dict)

        if current_sentence is not None:
            if current_words_in_sentence:
                current_words_in_sentence[-1]['end'] = audio_duration_ms
            current_sentence['end'] = audio_duration_ms
            current_sentence['words_in_sentence'] = current_words_in_sentence
            list_of_sentences.append(current_sentence)

        if list_of_sentences:
            list_of_sentences[-1]["is_last_sentence"] = True

        return list_of_sentences
    else:
        raise Exception("Could not retrieve speech marks")
