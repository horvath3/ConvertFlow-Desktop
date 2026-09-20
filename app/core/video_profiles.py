from __future__ import annotations

from dataclasses import dataclass

from app.core.performance_profiles import performance_profile


CONTAINER_CODECS: dict[str, list[str]] = {
    "mp4": ["H.264", "H.265 / HEVC", "AV1"],
    "mkv": ["H.264", "H.265 / HEVC", "AV1", "VP9"],
    "mov": ["H.264", "H.265 / HEVC"],
    "webm": ["VP9", "AV1"],
    "avi": ["H.264"],
}

CODEC_TO_FFMPEG = {
    "H.264": "libx264",
    "H.265 / HEVC": "libx265",
    "AV1": "libsvtav1",
    "VP9": "libvpx-vp9",
}

NVENC_CODECS = {
    "H.264": "h264_nvenc",
    "H.265 / HEVC": "hevc_nvenc",
    "AV1": "av1_nvenc",
}

CONVERT_CRF = {
    "Eredeti minőség": 17,
    "Kiváló minőség": 19,
    "Jó minőség": 21,
    "Kiegyensúlyozott": 24,
    "Kis fájlméret": 28,
    "Egyéni beállítások": 23,
}

H264_COMPRESS_CRF = {
    "Nagyon jó minőség": 18,
    "Jó minőség": 21,
    "Kiegyensúlyozott": 24,
    "Kis fájlméret": 27,
    "Maximális tömörítés": 30,
}

H265_COMPRESS_CRF = {
    "Nagyon jó minőség": 20,
    "Jó minőség": 23,
    "Kiegyensúlyozott": 26,
    "Kis fájlméret": 29,
    "Maximális tömörítés": 32,
}

NVENC_CQ = {
    "Nagyon jó minőség": 18,
    "Kiváló minőség": 19,
    "Jó minőség": 21,
    "Kiegyensúlyozott": 24,
    "Kis fájlméret": 28,
    "Maximális tömörítés": 31,
    "Eredeti minőség": 17,
    "Egyéni beállítások": 23,
}


@dataclass(frozen=True, slots=True)
class QualityArgs:
    codec: str
    args: list[str]


def quality_args(codec_label: str, profile: str, use_nvenc: bool = False, performance_mode: str = "Normál") -> QualityArgs:
    perf = performance_profile(performance_mode)
    if use_nvenc and codec_label in NVENC_CODECS:
        return QualityArgs(NVENC_CODECS[codec_label], ["-preset", perf.nvenc_preset, "-rc", "vbr", "-cq", str(NVENC_CQ.get(profile, 23))])
    codec = CODEC_TO_FFMPEG[codec_label]
    if codec_label == "H.265 / HEVC":
        crf = H265_COMPRESS_CRF.get(profile, CONVERT_CRF.get(profile, 23))
        return QualityArgs(codec, ["-preset", perf.cpu_preset, "-crf", str(crf)])
    if codec_label == "AV1":
        return QualityArgs(codec, ["-crf", str(CONVERT_CRF.get(profile, 28)), "-preset", "8"])
    if codec_label == "VP9":
        return QualityArgs(codec, ["-b:v", "0", "-crf", str(CONVERT_CRF.get(profile, 32))])
    crf = H264_COMPRESS_CRF.get(profile, CONVERT_CRF.get(profile, 23))
    return QualityArgs(codec, ["-preset", perf.cpu_preset, "-crf", str(crf)])
