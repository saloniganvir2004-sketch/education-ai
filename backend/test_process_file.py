from file_processor import process_file


text = process_file(
    "../uploads/sample.wav"
)

print(
    "PROCESSED TEXT:"
)

print(text)