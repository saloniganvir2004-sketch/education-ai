from subjects import SUBJECTS
from topics import TOPICS


def get_subjects():
    return SUBJECTS


def get_topics(subject: str):
    return TOPICS.get(subject, [])


def add_topic(subject: str, topic: str):
    if subject not in TOPICS:
        TOPICS[subject] = []

    if topic not in TOPICS[subject]:
        TOPICS[subject].append(topic)


def rename_topic(subject: str, old_topic: str, new_topic: str):
    if subject in TOPICS and old_topic in TOPICS[subject]:
        idx = TOPICS[subject].index(old_topic)
        TOPICS[subject][idx] = new_topic


def rename_subject(old_subject: str, new_subject: str):
    if old_subject in TOPICS:
        TOPICS[new_subject] = TOPICS.pop(old_subject)

    if old_subject in SUBJECTS:
        idx = SUBJECTS.index(old_subject)
        SUBJECTS[idx] = new_subject