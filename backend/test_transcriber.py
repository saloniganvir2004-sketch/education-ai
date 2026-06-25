from transcriber import transcribe_audio


text = transcribe_audio(
    "../uploads/sample.wav"
)

print(
    "TRANSCRIBED TEXT:"
)

print(text)