"""Shared media preparation. Every variant starts from the same source/master."""
import math
from pathlib import Path
import subprocess
from urllib.parse import quote


def probe(path, full_decode=False):
    import cv2
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot decode video: {path.name}")
    meta = dict(width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),fps=cap.get(cv2.CAP_PROP_FPS))
    try:
        if min(meta["width"],meta["height"]) < 1 or meta["frames"] < 8 or meta["fps"] <= 0:
            raise ValueError(f"Invalid source geometry/timing: {path.name}")
        if full_decode:
            count=0
            while cap.read()[0]:
                count+=1
            if count!=meta["frames"]:
                raise ValueError(f"Partial decode: {path.name} ({count}/{meta['frames']})")
    finally:
        cap.release()
    return meta

def read_exact_rgb(path, indices):
    """Decode all requested frames; reject partial decodes instead of padding."""
    import cv2
    cap = cv2.VideoCapture(str(path))
    wanted = set(indices)
    frames = {}
    try:
        if not cap.isOpened():
            raise ValueError(f"Cannot open {Path(path).name}")
        index = 0
        while len(frames) < len(wanted):
            ok, frame = cap.read()
            if not ok:
                break
            if index in wanted:
                frames[index] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            index += 1
        if set(frames) != wanted:
            raise ValueError(f"Missing sampled frames: {Path(path).name}")
        return [frames[i] for i in indices]
    finally:
        cap.release()


def transform_filter(name, width, height):
    if name == "identity":
        return None, (width, height)
    if name == "half_resize":
        return "scale=trunc(iw/4)*2:trunc(ih/4)*2:flags=bicubic", (width//4*2, height//4*2)
    if name == "center_crop_80":
        return "crop=trunc(iw*0.8/2)*2:trunc(ih*0.8/2)*2", (int(width*.8/2)*2, int(height*.8/2)*2)
    if name == "center_square":
        side = min(width, height)//2*2
        return f"crop={side}:{side}", (side, side)
    if name == "short_side_504":
        if min(width, height) < 504:
            raise ValueError("short_side_504 does not upscale")
        # FFmpeg -2 rounds the other dimension to the nearest multiple of two.
        other = lambda x, y: int(math.floor((x*504/y)/2 + .5))*2
        if width >= height:
            return "scale=-2:504:flags=bicubic", (other(width, height), 504)
        return "scale=504:-2:flags=bicubic", (504, other(height, width))
    raise ValueError("Unknown transform")


def prepare_cases(root, config, samples):
    from .artifacts import download, sha
    from .experiment import inside
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    sources = inside(root, config["source_directory"], "data")
    directory = root / f"data/experiments/{config['name']}"
    directory.mkdir(parents=True, exist_ok=True)
    cases, records = [], []
    for sample in samples:
        source = sources / f"{sample['id']}.mp4"
        url = f"https://huggingface.co/datasets/{sample['dataset']}/resolve/{sample['revision']}/{quote(sample['remote_path'], safe='/')}"
        download(url, source, sample["sha256"])
        native = probe(source, full_decode=True)
        if "actual_metadata" in sample and native != sample["actual_metadata"]:
            raise ValueError(f"Source metadata changed: {sample['id']}")
        commands, warnings = [], []

        def execute(command):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            commands.append([str(Path(a).relative_to(root)) if a.startswith(str(root)+"/") else a for a in command[1:]])
            warnings.append(result.stderr.strip().replace(str(root)+"/", ""))

        master, meta = source, native
        record = dict(video_id=sample["id"], source_sha256=sha(source), source_metadata=native)
        if config["preparation"] == "centered_4s_504_24fps":
            if min(native["width"], native["height"]) < 504 or native["width"] < native["height"] or native["fps"] < 24 or native["frames"]/native["fps"] < 4:
                raise ValueError("Common preparation needs landscape, >=504px, >=24fps, >=4 seconds")
            nominal_start = (native["frames"]/native["fps"] - 4)/2
            start = math.floor(nominal_start*native["fps"])/native["fps"]
            master = directory / f"{sample['id']}_master.avi"
            execute([ffmpeg, "-y", "-loglevel", "warning", "-ss", f"{start:.9f}", "-i", str(source), "-map", "0:v:0", "-an", "-vf",
                "setpts=PTS-STARTPTS,fps=24:start_time=0,scale=-2:504:flags=bicubic,crop=504:504,setsar=1,setpts=N/(24*TB)",
                "-frames:v", "96", "-c:v", "ffv1", "-pix_fmt", "yuv420p", str(master)])
            meta = probe(master, full_decode=True)
            if (meta["width"], meta["height"], meta["frames"]) != (504, 504, 96) or abs(meta["fps"]-24) > 1e-6:
                raise ValueError("Common master geometry/timing changed")
            record.update(nominal_center_start_seconds=nominal_start, start_seconds=start,
                          master_sha256=sha(master), master_metadata=meta)
        for variant in config["variants"]:
            filt, size = transform_filter(variant["transform"], meta["width"], meta["height"])
            if min(size) < 2:
                raise ValueError("Transform would produce an empty image")
            path = master
            if variant["encoding"] != "source":
                path = directory / f"{sample['id']}_{variant['name']}.{'avi' if variant['encoding']=='ffv1' else 'mp4'}"
                command = [ffmpeg, "-y", "-loglevel", "warning", "-i", str(master), "-map", "0:v:0", "-an"]
                if filt:
                    command += ["-vf", filt]
                if config["preparation"] != "native":
                    command += ["-frames:v", "96"]
                command += (["-c:v", "ffv1"] if variant["encoding"] == "ffv1" else
                            ["-c:v", "libx264", "-preset", "medium", "-crf", str(variant["crf"])])
                execute(command + ["-pix_fmt", "yuv420p", str(path)])
            info = probe(path, full_decode=True)
            if (info["width"], info["height"]) != size or info["frames"] != meta["frames"] or abs(info["fps"]-meta["fps"]) > .01:
                raise ValueError(f"Variant geometry or timing changed: {sample['id']}/{variant['name']}")
            cases.append((path, dict(video_id=sample["id"], label=sample["label"],
                source=sample.get("source", sample.get("generator", "")), cell=sample.get("cell", ""),
                content=sample.get("content", ""), variant=variant["name"], sha256=sha(path), **info)))
        records.append(record | dict(commands=commands, warnings=warnings))
        print(f"Prepared {sample['id']}: {len(config['variants'])} variants", flush=True)
    return cases, records
