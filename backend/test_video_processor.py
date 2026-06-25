from file_processor import process_video


text = process_video(
    "../uploads/sample.mp4"
)

print(
    "VIDEO TEXT:"
)

print(text)