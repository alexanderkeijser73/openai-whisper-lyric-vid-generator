import subprocess
from io import StringIO
from pathlib import Path
import os

import whisper
import whisper.utils
from pytube import YouTube

MODEL_VARIANT = "tiny"  # "medium" and "large" are really good but require a GPU

out_dir = Path.cwd()
audio_path = out_dir / "audio_out.mp3"
srt_path = out_dir / "lyrics_out.srt"
video_path = out_dir / "video_out.mp4"
final_vid_path = out_dir / "final_vid.mp4"


def download_vid_and_audio(youtube_url: str):
    youtube = YouTube(youtube_url)

    audio_stream = (
        youtube.streams.filter(only_audio=True, audio_codec="opus")
        .order_by("bitrate")
        .last()
    )

    audio_stream.download(
        output_path=os.path.dirname(audio_path), filename=os.path.basename(audio_path)
    )

    # get the lowest quality video stream
    # video_stream = youtube.streams.filter(file_extension='mp4').order_by('resolution').first()

    video_stream = youtube.streams.get_by_itag(18)  ##### itag 18 also seems to be good

    video_stream.download(
        output_path=os.path.dirname(video_path), filename=os.path.basename(video_path)
    )


def write_srt(result):
    with open(srt_path, "w") as f:
        whisper.utils.write_srt(result["segments"], f)


def print_lyrics(result):
    buffer = StringIO()
    whisper.utils.write_txt(result["segments"], buffer)
    print(buffer.getvalue())


def write_lyrics_to_vid(srt_path, vid_path, final_vid_path, mode="hard"):
    # https://trac.ffmpeg.org/wiki/HowToBurnSubtitlesIntoVideo
    # https://stackoverflow.com/questions/8672809/use-ffmpeg-to-add-text-subtitles

    commands = {
        "optional": [
            "ffmpeg",
            "-y",
            "-i",
            vid_path,
            "-i",
            srt_path,
            "-c",
            "copy",
            "-c:s",
            "mov_text",
            final_vid_path,
        ],
        "hard": [
            "ffmpeg",
            "-y",
            "-i",
            vid_path,
            "-vf",
            f"subtitles={srt_path}",
            final_vid_path,
        ],
    }

    valid_options = set(commands.keys())
    if not mode in valid_options:
        raise ValueError(f"Mode '{mode}' not recognized, choose one of {valid_options}")

    result = subprocess.run(commands[mode], capture_output=True)

    print(result.stdout.decode())
    print(result.stderr.decode())


if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=ThCbl10-1pA&ab_channel=COLORS"

    download_vid_and_audio(youtube_url)

    model = whisper.load_model(MODEL_VARIANT)
    result = model.transcribe(str(audio_path))

    write_srt(result)
    print_lyrics(result)

    write_lyrics_to_vid(srt_path, video_path, final_vid_path, mode="optional")
