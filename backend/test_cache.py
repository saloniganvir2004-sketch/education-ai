from cache import (
    get_cached_answer,
    set_cached_answer
)

set_cached_answer(
    "What is AI?",
    "Artificial Intelligence is the simulation of human intelligence."
)

answer = get_cached_answer(
    "What is AI?"
)

print(answer)