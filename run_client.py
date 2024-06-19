import sys
import threading
from time import sleep
import configparser
import os.path

from whisper_live.client import TranscriptionClient
from whisper_live.device_type_enum import DeviceType
import whisper_live.utils as utils

clients = []
restart_counter = 0
files_collection = []
config = configparser.ConfigParser()


def load_configs(filename):
    global config

    # output default config file if not
    if not os.path.isfile(filename):
        config['Websocket'] = {'Host': 'localhost', 'Port': 9090}
        config['Client'] = {
            'TranscribeMicrophone': 'True',
            'TranscribePcAudio': 'True',
            'Language': 'en',
            'Translate': 'False',
            'Model': 'small',
            'VoiceActivationDetection': 'True',
            'SaveMicrophoneWavFile': 'False',
            'SavePcAudioWavFile': 'False'
        }
        with open(filename, 'w') as configfile:
            config.write(configfile)

    # load config
    config.read(filename)

    # add defaults
    # config['DEFAULT'] = {
    #     'TranscribeMicrophone': 'True',
    #     'TranscribePcAudio': 'True',
    #     'SaveMicrophoneWavFile': 'False',
    #     'SavePcAudioWavFile': 'False'
    # }
    return config


def start_client(device_type, save_output_recording, output_transcription_path, output_recording_filename):
    global clients
    # instantiate client
    client = TranscriptionClient(
        config.get('Websocket', 'Host', fallback='localhost'),
        config.getint('Websocket', 'Port', fallback=9090),
        lang=config.get('Client', 'Language', fallback='en'),
        translate=config.getboolean('Client', 'Translate', fallback=False),
        model=config.get('Websocket', 'Model', fallback='small'),
        use_vad=config.getboolean('Client', 'VoiceActivationDetection', fallback=True),
        device_type=device_type,
        save_output_recording=save_output_recording,
        output_transcription_path=output_transcription_path,
        output_recording_filename=output_recording_filename
    )
    clients.append(client)
    # start client
    client()


def merge_and_concatenate(files):
    """
    Merge all files and concatenate them into one srt file, with the subtitle source specified.
    :param files:
    :return:
    """
    merged_files = []
    for index in range(len(files)):
        output_file_name = "srt-files/merged/merged" + str(index) + ".srt"
        utils.merge_srt_files(files[index], output_file_name, True)
        merged_files.append(output_file_name)

    # concatenate srt files
    if len(merged_files) > 1:
        utils.concatenate_srt_files(merged_files, "srt-files/transcription.srt")


def start_application(speaker_thread=None, microphone_thread=None):
    """
    Instantiates a computer speaker and microphone transcription clients threads,
    and ensures they remain alive until further notice.
    :param speaker_thread:
    :param microphone_thread:
    :return:
    """
    global restart_counter
    global files_collection
    restart_counter += 1
    files = []

    # if either thread is not active, start it
    if (config.getboolean('Client', 'TranscribePcAudio', fallback=True) and
            (not speaker_thread or not speaker_thread.is_alive())):
        srt_file_name = "./srt-files/pc-audio/audio" + str(restart_counter) + ".srt"
        wav_file_name = "./wav-files/pc-audio/audio" + str(restart_counter) + ".wav"
        speaker_thread = threading.Thread(
            target=start_client,
            args=(DeviceType.OUTPUT, config.getboolean('Client', 'SavePcAudioWavFile', fallback=False), srt_file_name, wav_file_name)
        )
        speaker_thread.start()
        files.append(srt_file_name)
    if (config.getboolean('Client', 'TranscribeMicrophone', fallback=True) and
            (not microphone_thread or not microphone_thread.is_alive())):
        srt_file_name = "./srt-files/microphone/microphone" + str(restart_counter) + ".srt"
        wav_file_name = "./srt-files/microphone/microphone" + str(restart_counter) + ".wav"
        microphone_thread = threading.Thread(
            target=start_client,
            args=(DeviceType.INPUT, config.getboolean('Client', 'SaveMicrophoneWavFile', fallback=False), srt_file_name, wav_file_name)
        )
        microphone_thread.start()
        files.append(srt_file_name)

    try:
        # wait for a thread to die
        while speaker_thread.is_alive() and microphone_thread.is_alive():
            speaker_thread.join(timeout=1)
            microphone_thread.join(timeout=1)
        files_collection.append(files)
        # rerun app (restart the dead threads, keep the alive ones)
        start_application(speaker_thread=speaker_thread, microphone_thread=microphone_thread)
    except KeyboardInterrupt:
        # gracefully stop
        for client in clients:
            client.stop()
        sleep(2)
        files_collection.append(files)
        merge_and_concatenate(files_collection)
        sys.exit(0)


load_configs('config.ini')
start_application()
