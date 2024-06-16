import sys
import threading
from time import sleep

from whisper_live.client import TranscriptionClient
from whisper_live.device_type_enum import DeviceType
import whisper_live.utils as utils

clients = []
restart_counter = 0
files_collection = []


def start_client(device_type, save_output_recording, output_transcription_path, output_recording_filename):
    global clients
    client = TranscriptionClient(
        "localhost",
        9090,
        lang="it",
        translate=False,
        model="small",
        use_vad=True,
        device_type=device_type,
        save_output_recording=save_output_recording,
        output_transcription_path=output_transcription_path,
        output_recording_filename=output_recording_filename
    )
    clients.append(client)
    client()


def merge_and_concatenate(files):
    """
    Merge all files and concatenate them into one srt file, with the subtitle source specified.
    :param files:
    :return:
    """
    merged_files = []
    for index in range(len(files)):
        output_file_name = "merged" + str(index) + ".srt"
        utils.merge_srt_files(files[index], output_file_name, True)
        merged_files.append(output_file_name)

    # concatenate srt files
    if len(merged_files) > 1:
        utils.concatenate_srt_files(merged_files, "out.srt")


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
    if not speaker_thread or not speaker_thread.is_alive():
        file_name = "./audio" + str(restart_counter) + ".srt"
        speaker_thread = threading.Thread(
            target=start_client,
            args=(DeviceType.OUTPUT, False, file_name, "")
        )
        speaker_thread.start()
        files.append(file_name)
    if not microphone_thread or not microphone_thread.is_alive():
        file_name = "./microphone" + str(restart_counter) + ".srt"
        microphone_thread = threading.Thread(
            target=start_client,
            args=(DeviceType.INPUT, False, file_name, "")
        )
        microphone_thread.start()
        files.append(file_name)

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


start_application()
