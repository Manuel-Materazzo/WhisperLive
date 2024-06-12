import os
import textwrap
import scipy.io.wavfile
import scipy.signal
import ffmpeg
import numpy as np


def clear_screen():
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_transcript(text):
    """Prints formatted transcript text."""
    wrapper = textwrap.TextWrapper(width=60)
    for line in wrapper.wrap(text="".join(text)):
        print(line)


def format_time(s):
    """Convert seconds (float) to SRT time format."""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    milliseconds = int((s - int(s)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def create_srt_file(segments, output_file):
    with open(output_file, 'w', encoding='utf-8') as srt_file:
        segment_number = 1
        for segment in segments:
            start_time = format_time(float(segment['start']))
            end_time = format_time(float(segment['end']))
            text = segment['text']

            srt_file.write(f"{segment_number}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")

            segment_number += 1


def resample(file: str, sr: int = 16000):
    """
    # https://github.com/openai/whisper/blob/7858aa9c08d98f75575035ecd6481f462d66ca27/whisper/audio.py#L22
    Open an audio file and read as mono waveform, resampling as necessary,
    save the resampled audio

    Args:
        file (str): The audio file to open
        sr (int): The sample rate to resample the audio if necessary

    Returns:
        resampled_file (str): The resampled audio file
    """
    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        out, _ = (
            ffmpeg.input(file, threads=0)
            .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e
    np_buffer = np.frombuffer(out, dtype=np.int16)

    resampled_file = f"{file.split('.')[0]}_resampled.wav"
    scipy.io.wavfile.write(resampled_file, sr, np_buffer.astype(np.int16))
    return resampled_file


def resample_stream(data, old_rate: int, new_rate: int = 16000, num_channels: int = 1):
    """
    Open an audio stream and read as mono waveform, resampling as necessary,
    returns the resampled audio

    Args:
        data : The data of the audio stream
        old_rate (int): The old sample rate
        new_rate (int): The sample rate to resample the audio if necessary
        num_channels (int): The number of channels in the audio data
    Returns:
        resampled_file: The resampled audio stream
    """
    try:
        numpy_data = np.frombuffer(data, dtype=np.int16)

        # Check if the data has more than 1 channel
        if num_channels > 1:
            # Reshape the data into a 2D array and take the mean of the channels to convert to mono
            numpy_data = numpy_data.reshape(-1, num_channels)
            mono_data = np.mean(numpy_data, axis=1)
        else:
            # If the data is already mono, no need to take the mean
            mono_data = numpy_data

        resample_ratio = new_rate / old_rate

        # Ensure the new length is a multiple of 2
        new_length = int(len(mono_data) * resample_ratio)
        if new_length % 2 != 0:
            new_length += 1

        resampled_data = scipy.signal.resample(mono_data, new_length)
        return resampled_data.astype(np.int16).tobytes()

    except Exception as e:
        raise RuntimeError(f"Failed to resample audio") from e
