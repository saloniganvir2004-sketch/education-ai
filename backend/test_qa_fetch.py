from qa_db import get_all_qa_pairs

records = get_all_qa_pairs()

for row in records:
    print(row)