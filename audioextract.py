import subprocess
import string
import json
import sys
import os


def fixpath(path: str) -> str:
    if sys.platform != "win32":
        return path

    # turn paths like /c/something /d/something, etc. into proper window paths
    if path[0] == "/" and path[1] in string.ascii_lowercase and path[2] == "/":
        return path[1].upper() + ":" + path[2:]

    return path


MAPPINGS = {
    "opus": "opus",
    "vorbis": "ogg",
    "mp3": "mp3",
    "aac": "aac",
}

FFMPEG_ARGS = ("ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-i")


def prettysize(fsize: int) -> str:
    if fsize == 1:
        return "1 Byte"
    if fsize < 1024:
        return f"{fsize} Bytes"
    if fsize < 1024 * 1024:
        return f"{fsize / 1024:.1f} KiB"
    if fsize < 1024 * 1024 * 1024:
        return f"{fsize / (1024 * 1024):.1f} MiB"
    return f"{fsize / (1024 * 1024 * 1024):.1f} GiB"


def main():

    for pa in sys.argv[1:]:
        pa = fixpath(pa)
        pasize = os.path.getsize(pa)
        r = subprocess.run(FFMPEG_ARGS + (pa,), stdout=subprocess.PIPE, check=True)
        data = json.loads(r.stdout)

        for x in data["streams"]:
            if x["codec_type"] != "audio":
                continue

            codec = x["codec_name"]
            if codec not in MAPPINGS:
                print(f"unknown codec {codec} - can't figure out an extension - {pa}")

            barename = os.path.splitext(os.path.split(pa)[1])[0]
            outname = f"{barename}.{MAPPINGS[codec]}"

            args = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-stats",
                "-i",
                pa,
                "-vn",
                "-acodec",
                "copy",
                outname,
            ]
            print(args)
            subprocess.run(args, check=True)
            outsize = os.path.getsize(outname)

            # NOTE: newline is to part a bit away from output of stdout and stderr of ffmpeg
            print(
                f"\nConverted {pa} to {outname} from {prettysize(pasize)} to {prettysize(outsize)} aka {100.0 * outsize / pasize:.2f}%"
            )
            break  # TODO: dont break after one stream but extract all audios? hmm...


if __name__ == "__main__":
    main()
