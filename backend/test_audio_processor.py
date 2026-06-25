from file_processor import process_audio


text = process_audio(
    "../uploads/sample.wav"
)

print(
    "AUDIO TEXT:"
)

print(text)