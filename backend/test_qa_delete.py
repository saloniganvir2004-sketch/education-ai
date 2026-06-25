from qa_db import get_all_qa_pairs
from qa_db import delete_qa_pair


records = get_all_qa_pairs()

if records:

    latest_id = records[-1][0]

    delete_qa_pair(
        latest_id
    )

    print(
        f"Deleted QA ID: {latest_id}"
    )

else:

    print(
        "No records found"
    )