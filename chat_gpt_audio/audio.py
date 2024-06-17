# Copyright 2023 Figure AI, Inc

import dataclasses
import logging
import os
import pathlib
import queue
import tempfile
import threading
import time
import wave
from typing import Any, Callable, Optional

import pyaudio
import pydub
from pydub import AudioSegment

# from python_modules.manipulation.sensors.pedals.usb_pedal import UsbPedal

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SpeakerInfo:
    name: str
    device_index: int
    channels: int
    rate: int


def get_audio_devices(audio: Optional[pyaudio.PyAudio] = None) -> dict[str, Any]:
    if audio is None:
        audio = pyaudio.PyAudio()

    while True:
        try:
            num_devices = audio.get_device_count()
        except OSError:
            logger.error("Failed to get device count. Trying again...")
            time.sleep(0.1)
            continue
        break

    devices = {}
    for i in range(min(30, num_devices)):
        try:
            info = audio.get_device_info_by_index(i)
        except OSError:
            continue
        devices[info["name"]] = info

    return devices


class AudioPlayer:
    def __init__(
        self,
        device: Optional[str] = "HDA Intel PCH: ALC897 Analog",
        *,
        chunk: int = 512,
        multithreaded: bool = False,
    ) -> None:
        if multithreaded:
            self._play_queue = queue.Queue[tuple[Optional[str], Optional[Callable[[], None]]]]()
            self._finished_queue = queue.Queue[Optional[str]]()
            self._thread = threading.Thread(
                target=AudioPlayer.run_thread, args=(self._play_queue, self._finished_queue)
            )
            self._thread.start()
        else:
            self._thread = None
            self.chunk = chunk
            self.audio = pyaudio.PyAudio()
            self.speaker_info = (
                self.audio.get_default_input_device_info()
                if device is None
                else self._find_speaker(device)
            )
            self._stream: Optional[pyaudio.Stream] = None
            self._wf: Optional[wave.Wave_read] = None

    def is_async_playing(self) -> bool:
        return False if self._stream is None else self._stream.is_active()

    def _find_speaker(self, name_hint: str) -> SpeakerInfo:
        devices = get_audio_devices(self.audio)
        # print(devices)
        for device_name, device_info in devices.items():
            if name_hint in device_name:  # pyright: ignore[reportGeneralTypeIssues]
                return SpeakerInfo(
                    name=device_name,
                    device_index=device_info["index"],  # pyright: ignore[reportGeneralTypeIssues]
                    channels=device_info["maxOutputChannels"],  # pyright: ignore[reportGeneralTypeIssues]
                    rate=int(
                        device_info["defaultSampleRate"] + 0.5  # pyright: ignore[reportGeneralTypeIssues]
                    ),
                )

        raise RuntimeError(f"Could not find audio device {name_hint}")

    def _convert_to_wav(self, audio_path) -> pathlib.Path:
        audio_path = pathlib.Path(audio_path)
        if audio_path.suffix == ".mp3":
            audio = AudioSegment.from_mp3(audio_path)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            audio.export(temp_file.name, format="wav")
            return pathlib.Path(temp_file.name)
        return audio_path

    def _resample_audio(self, audio_path, target_rate: int) -> str:
        sound = pydub.AudioSegment.from_wav(str(audio_path))
        resampled_sound = sound.set_frame_rate(target_rate)
        new_file_path = "resampled_" + pathlib.Path(audio_path).name
        resampled_sound.export(new_file_path, format="wav")
        return new_file_path

    def play(self, audio_path) -> None:
        if self._thread is not None:
            self._play_queue.put((str(audio_path), None))
            while self._finished_queue.get() != str(audio_path):
                continue
            return
        self.close()

        wav_file = self._convert_to_wav(audio_path)
        with wave.open(str(wav_file), "rb") as wf:
            file_rate = wf.getframerate()
            supported_rates = [48000]

            if file_rate not in supported_rates:
                wav_file = self._resample_audio(wav_file, supported_rates[0])
                # TODO(toki): get context manager for second wf
                wf = wave.open(wav_file, "rb")  # Reopen the resampled file

            try:
                output_device_index: Optional[int] = self.speaker_info.device_index  # pyright: ignore[reportAttributeAccessIssue,reportGeneralTypeIssues]
            except AttributeError:
                output_device_index = None
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),  # Now this will be the correct rate
                output=True,
                output_device_index=output_device_index,
            )

            while len(data := wf.readframes(self.chunk)):
                stream.write(data)

            stream.close()
            wf.close()  # Close the wave file

        if pathlib.Path(audio_path).suffix == ".mp3":
            os.remove(wav_file)  # Clean up the temporary WAV file

    def close(self) -> None:
        if self._thread is not None:
            self._play_queue.put((None, None))
            self._thread.join()
            return

        while self.is_async_playing():
            time.sleep(0.01)
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        self._stream = None
        if self._wf is not None:
            self._wf.close()
        self._wf = None

    def play_async(
        self, audio_path, callback_fn: Optional[Callable[[], None]] = None
    ) -> None:
        if self._thread is not None:
            self._play_queue.put((str(audio_path), callback_fn))
            return

        def callback(
            in_data: Any, frame_count: int, time_info: Any, status: Any
        ) -> tuple[bytes, int]:
            assert self._wf is not None
            data = self._wf.readframes(frame_count)
            # If len(data) is less than requested frame_count, PyAudio automatically
            # assumes the stream is finished, and the stream stops.
            if len(data) < frame_count and callback_fn is not None:
                logger.info("CALLBACK")
                callback_fn()

            return data, pyaudio.paContinue

        self.close()
        wav_file = self._convert_to_wav(audio_path)

        self._wf = wave.open(str(wav_file), "rb")
        file_rate = self._wf.getframerate()
        supported_rates = [48000]

        if file_rate not in supported_rates:
            wav_file = self._resample_audio(wav_file, supported_rates[0])
            self._wf.close()
            self._wf = wave.open(wav_file, "rb")  # Reopen the resampled file

        try:
            output_device_index: Optional[int] = self.speaker_info.device_index  # pyright: ignore[reportAttributeAccessIssue,reportGeneralTypeIssues]
        except AttributeError:
            output_device_index = None
        try:
            self._stream = self.audio.open(
                format=self.audio.get_format_from_width(self._wf.getsampwidth()),
                channels=self._wf.getnchannels(),
                rate=self._wf.getframerate(),  # Now this will be the correct rate
                output=True,
                output_device_index=output_device_index,
                stream_callback=callback,
            )
        except OSError:
            logger.warning("Failed to open audio. Trying again...")
            self.audio.terminate()
            self.audio = pyaudio.PyAudio()
            self._stream = self.audio.open(
                format=self.audio.get_format_from_width(self._wf.getsampwidth()),
                channels=self._wf.getnchannels(),
                rate=self._wf.getframerate(),  # Now this will be the correct rate
                output=True,
                output_device_index=output_device_index,
                stream_callback=callback,
            )

    @staticmethod
    def run_thread(
        play_queue: queue.Queue[tuple[Optional[str], Optional[Callable[[], None]]]],
        finished_queue: queue.Queue[Optional[str]],
    ) -> None:
        audio = AudioPlayer()
        while True:
            audio_path, callback_fn = play_queue.get()
            if audio_path is None:
                logger.info("Exiting audio thread")
                finished_queue.put(None)
                break
            else:
                logger.info(f"Playing {audio_path}")
            audio.play(audio_path)
            logger.info(f"Finished {audio_path}")
            if callback_fn is not None:
                callback_fn()
            finished_queue.put(audio_path)


class AudioRecorder:
    def __init__(
        self,
        format: int = pyaudio.paInt16,
        channels: int = 2,
        rate: int = 44100,
        chunk: int = 1024,
        # use_pedal: bool = True,
        device: str = "MacBook Pro Microphone",
    ) -> None:
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.device = device

        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.frames = []
        self.stream = None
        self.record_thread = None
        self.device_index = self._get_local_mic_index()
        # if use_pedal:
        #     self.pedal = UsbPedal()

    def _get_local_mic_index(self) -> int:
        names = get_audio_devices(self.audio).keys()
        print(names)
        for i, name in enumerate(names):
            # import pdb; pdb.set_trace()
            if self.device not in name:
                continue
            try:
                stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=self.chunk,
                )
            except OSError as e:
                print("OS Error!!!")
                print(e)
                continue
            else:
                stream.close()

            return i
        raise ValueError(f"Could not find {self.device} device index.")

    def _record_loop(self) -> None:
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk,
        )
        while self.recording:
            try:
                if not stream.is_active():
                    print("Stream not active!!!")
                    break
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                # print("data:", data)
            except Exception as e:
                print(f"Error while reading audio stream: {e}")
                break

        print("Stopping and closing stream ...")
        stream.stop_stream()
        stream.close()

    def begin_record_audio(self) -> None:
        self.t_start = time.time()
        print("Recording started...")
        self.recording = True
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()
        # self._record_loop()

    def end_record_audio(self, wav_path = None) -> Optional[str]:
        print("Recording stopped")
        self.recording = False
        if self.record_thread is not None:
            self.record_thread.join()

        if time.time() - self.t_start < 1.0:
            print("Recording too short. Try again.")
            return None

        # Save the recorded data as a WAV file
        if wav_path is None:
            wav_path = tempfile.mktemp(suffix=".wav")
        wav_path = str(wav_path)
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b"".join(self.frames))
        self.frames = []  # Clear the frames for the next recording
        # Log file path and size
        file_size = os.path.getsize(wav_path)
        print(f"File saved: {wav_path}, Size: {file_size/1e+6} mb")
        return wav_path

    def close(self) -> None:
        self.audio.terminate()

    def wait_for_recorded_file(
        self,
        on_record_callback: Optional[Callable[[], None]] = None,
        # wav_path: Optional[pathlib.Path | str] = None,
        wav_path: str = "",
    ) -> Optional[str]:
        # Wait for right pedal down.
        print("AudioRecorder: Press and hold left pedal to start recording. Release to stop.")
        # while not self.pedal.left_pressed:
        #     if self.pedal.middle_pressed:
        #         raise StopIteration
        #     time.sleep(0.01)

        if on_record_callback is not None:
            on_record_callback()
        self.begin_record_audio()

        # Wait for right pedal up.
        # print("AudioRecorder: Release left pedal to stop recording.")
        # while self.pedal.left_pressed:
        #     time.sleep(0.01)
        t_wait = 5.0
        print(f"Waiting for {t_wait} seconds")
        t_start = time.time()
        while time.time() - t_start < t_wait:
            time.sleep(0.5)
        print("Wait time finished!!")

        return self.end_record_audio(wav_path=wav_path)