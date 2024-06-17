from audio import AudioRecorder


if __name__ == "__main__":

	wav_path = "/Users/alonrot/artistic/chat_gpt_audio/messages/test/test.mp3"
	recorder = AudioRecorder(channels=1)
	recorder.wait_for_recorded_file(wav_path=wav_path)
