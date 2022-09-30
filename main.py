import subprocess
from io import StringIO
from pathlib import Path
from typing import Dict, Union

import whisper
import whisper.utils
from pytube import YouTube

WhisperResult = Dict[str, Union[str, list, dict]]

MODEL_VARIANT = "tiny"  # "medium" and "large" are really good but require a GPU


def download_vid_and_audio(
    youtube_url: str, video_path: Path, audio_path: Path
) -> None:
    youtube = YouTube(youtube_url)

    audio_stream = (
        youtube.streams.filter(only_audio=True, audio_codec="opus")
        .order_by("bitrate")
        .last()
    )

    audio_stream.download(
        output_path=str(audio_path.parent), filename=str(audio_path.name)
    )

    # get the lowest quality video stream
    # video_stream = youtube.streams.filter(file_extension='mp4').order_by('resolution').first()

    video_stream = youtube.streams.get_by_itag(18)  ##### itag 18 also seems to be good

    video_stream.download(
        output_path=str(video_path.parent), filename=str(video_path.name)
    )


def write_srt(result: WhisperResult) -> None:
    with open(srt_path, "w") as f:
        whisper.utils.write_srt(result["segments"], f)


def print_lyrics(result: WhisperResult):
    buffer = StringIO()
    whisper.utils.write_txt(result["segments"], buffer)
    print(buffer.getvalue())


def write_lyrics_to_vid(
    srt_path: Path, vid_path: Path, final_vid_path: Path, srt_write_mode: str = "hard"
) -> None:
    # https://trac.ffmpeg.org/wiki/HowToBurnSubtitlesIntoVideo
    # https://stackoverflow.com/questions/8672809/use-ffmpeg-to-add-text-subtitles

    commands = {
        "optional": f"ffmpeg -y -i {vid_path} -i {srt_path} -c copy -c:s mov_text {final_vid_path}",
        "hard": f"ffmpeg -y -i {vid_path} -vf subtitles={srt_path} final_vid_path",
    }

    valid_options = set(commands.keys())
    if not srt_write_mode in valid_options:
        raise ValueError(
            f"Mode '{srt_write_mode}' not recognized, choose one of {valid_options}"
        )

    out = subprocess.run(commands[srt_write_mode].split(), capture_output=True)

    print(out.stdout.decode())
    print(out.stderr.decode())


def main(
    youtube_url: str,
    video_path: Path,
    audio_path: Path,
    final_vid_path: Path,
    model_variant: str = MODEL_VARIANT,
) -> None:
    download_vid_and_audio(youtube_url, video_path, audio_path)

    model = whisper.load_model(model_variant)
    result: WhisperResult = model.transcribe(str(audio_path))

    write_srt(result)
    print_lyrics(result)

    write_lyrics_to_vid(srt_path, video_path, final_vid_path, srt_write_mode="optional")


if __name__ == "__main__":

    out_dir = Path.cwd()
    audio_path = out_dir / "audio_out.mp3"
    srt_path = out_dir / "lyrics_out.srt"
    video_path = out_dir / "video_out.mp4"
    final_vid_path = out_dir / "final_vid.mp4"

    youtube_url = "https://www.youtube.com/watch?v=ThCbl10-1pA&ab_channel=COLORS"

    main(youtube_url, video_path, audio_path, final_vid_path)
