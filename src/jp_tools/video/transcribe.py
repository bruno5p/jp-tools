try:
    import torch
    from transformers import pipeline
    from transformers.utils import is_flash_attn_2_available
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}\n  pip install 'jp-tools[transcribe]'") from e

_MODEL_ID = "kotoba-tech/kotoba-whisper-v2.2"


class Transcriber:
    def __init__(self, model=_MODEL_ID, device=None):
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading ASR model: {model}  (device={device}) ...")
        self._pipe = self._build_pipe(model, device)

    @staticmethod
    def _build_pipe(model_id, device):
        attn = "flash_attention_2" if is_flash_attn_2_available() else "sdpa"
        dtype = torch.float16 if device != "cpu" else torch.float32
        return pipeline(
            "automatic-speech-recognition",
            model=model_id,
            dtype=dtype,
            device=device,
            model_kwargs={"attn_implementation": attn},
        )

    @staticmethod
    def _srt_ts(seconds):
        if seconds is None:
            seconds = 0.0
        ms = int(round((seconds % 1) * 1000))
        total_s = int(seconds)
        h, rem = divmod(total_s, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _format_srt(result):
        chunks = result.get("chunks", [])
        if not chunks:
            text = result.get("text", "").strip()
            return f"1\n00:00:00,000 --> 00:00:00,000\n{text}\n"
        blocks = []
        for idx, chunk in enumerate(chunks, start=1):
            ts = chunk["timestamp"]
            start = Transcriber._srt_ts(ts[0])
            end = Transcriber._srt_ts(ts[1])
            text = chunk["text"].strip()
            blocks.append(f"{idx}\n{start} --> {end}\n{text}")
        return "\n\n".join(blocks) + "\n"

    def transcribe(self, audio_path) -> str:
        """Transcribe audio file and return SRT content as a string."""
        result = self._pipe(
            audio_path,
            return_timestamps=True,
            generate_kwargs={"language": "japanese", "task": "transcribe"},
        )
        return self._format_srt(result)
