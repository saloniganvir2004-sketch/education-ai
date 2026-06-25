from main import generate_answer


questions = [
    "What is Artificial Intelligence?",
    "Explain Machine Learning",
    "Who is mentioned in the uploaded content?",
    "Summarize the uploaded content"
]


for question in questions:

    print("\n" + "=" * 80)

    print(
        "QUESTION:",
        question
    )

    answer = generate_answer(
        question=question,
        user_id="test_user"
    )

    print(
        "ANSWER:",
        answer
    )