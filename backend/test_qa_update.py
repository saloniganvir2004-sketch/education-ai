from qa_db import add_qa_pair
from qa_db import update_qa_pair
from qa_db import get_all_qa_pairs


add_qa_pair(
    question="What is AI?",
    answer="Old Answer"
)

records = get_all_qa_pairs()

latest_id = records[-1][0]

update_qa_pair(
    qa_id=latest_id,
    question="What is AI?",
    answer="Artificial Intelligence is the simulation of human intelligence."
)

print(
    get_all_qa_pairs()
)