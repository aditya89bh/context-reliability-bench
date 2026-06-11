"""Generate fixtures/v1/large_dataset.json with 500 benchmark cases."""

from __future__ import annotations

import json
from pathlib import Path

_TOPICS = [
    (
        "astronomy",
        "What is the distance from Earth to the Moon in kilometres?",
        "The average distance from Earth to the Moon is approximately 384,400 km,"
        " varying between 356,500 km at perigee and 406,700 km at apogee.",
    ),
    (
        "biology",
        "What is the function of mitochondria in a cell?",
        "Mitochondria are membrane-bound organelles that generate most of the"
        " cell's ATP through oxidative phosphorylation, the powerhouse of the cell.",
    ),
    (
        "chemistry",
        "What is the chemical formula for glucose?",
        "Glucose has the molecular formula C6H12O6. It is a simple sugar and the"
        " primary source of energy for living organisms.",
    ),
    (
        "history",
        "When did the First World War begin?",
        "The First World War began on 28 July 1914, following the assassination"
        " of Archduke Franz Ferdinand of Austria on 28 June 1914.",
    ),
    (
        "geography",
        "What is the longest river in the world?",
        "The Nile River is traditionally considered the longest river in the world"
        " at approximately 6,650 kilometres.",
    ),
    (
        "physics",
        "What is the speed of light in a vacuum?",
        "The speed of light in a vacuum is exactly 299,792,458 metres per second,"
        " often approximated as 3 x 10^8 m/s.",
    ),
    (
        "mathematics",
        "What is Euler's number e to 5 decimal places?",
        "Euler's number e is approximately 2.71828. It is the base of the natural"
        " logarithm and arises in continuous compounding and calculus.",
    ),
    (
        "literature",
        "Who wrote the novel Pride and Prejudice?",
        "Pride and Prejudice was written by Jane Austen and published in 1813,"
        " following Elizabeth Bennet and Mr Darcy.",
    ),
    (
        "computer_science",
        "What does CPU stand for?",
        "CPU stands for Central Processing Unit. It is the primary component of a"
        " computer that executes instructions and arithmetic operations.",
    ),
    (
        "medicine",
        "What is the normal resting heart rate for adults?",
        "A normal resting heart rate for adults ranges from 60 to 100 beats per"
        " minute. Athletes may have rates below 60 bpm.",
    ),
]

_DISTRACTORS = [
    "Photosynthesis converts carbon dioxide and water into glucose using sunlight"
    " energy captured by chlorophyll in plant chloroplasts.",
    "The Pythagorean theorem states that in a right triangle the square of the"
    " hypotenuse equals the sum of squares of the other two sides.",
    "Ocean salinity averages about 35 parts per thousand, primarily from dissolved"
    " sodium chloride, affecting seawater density and circulation.",
    "Plate tectonics describes the movement of large sections of Earth's crust,"
    " driving continental drift, earthquakes, and volcanic activity.",
    "The French Revolution began in 1789 and led to the overthrow of the monarchy"
    " and the rise of Napoleon Bonaparte.",
    "Neural networks in machine learning are computational models loosely inspired"
    " by biological neurons, used for pattern recognition.",
    "The periodic table organises chemical elements by atomic number, electron"
    " configuration, and recurring chemical properties.",
    "Climate change refers to long-term shifts in global temperatures driven"
    " primarily by human emissions of greenhouse gases.",
    "Supply and demand is a fundamental economic model describing how price"
    " changes in response to consumer demand and producer supply.",
    "The Renaissance was a cultural movement in Europe between the 14th and 17th"
    " centuries, marked by renewed interest in classical antiquity.",
]


def _build_case(idx: int) -> dict:  # type: ignore[type-arg]
    topic_idx = idx % len(_TOPICS)
    topic, query_text, relevant_content = _TOPICS[topic_idx]

    relevant_doc_id = f"ld-{idx:04d}-d1"
    docs = [
        {
            "document": {
                "id": relevant_doc_id,
                "content": relevant_content,
                "metadata": {"topic": topic, "relevant": True},
            },
            "score": round(0.90 - (idx % 5) * 0.01, 4),
            "rank": 1,
        }
    ]

    for j in range(4):
        distractor = _DISTRACTORS[(idx + j) % len(_DISTRACTORS)]
        docs.append(
            {
                "document": {
                    "id": f"ld-{idx:04d}-d{j+2}",
                    "content": distractor,
                    "metadata": {"topic": "distractor", "relevant": False},
                },
                "score": round(0.70 - j * 0.05, 4),
                "rank": j + 2,
            }
        )

    return {
        "id": f"ld-{idx:04d}",
        "query": {"id": f"q-ld-{idx:04d}", "text": query_text},
        "context": docs,
        "relevant_doc_ids": [relevant_doc_id],
        "expected_answer": relevant_content[:80],
    }


def main() -> None:
    out = Path(__file__).parent.parent / "fixtures" / "v1" / "large_dataset.json"
    cases = [_build_case(i) for i in range(500)]
    fixture = {
        "format_version": "1.0",
        "category": "large_dataset",
        "description": "500-case fixture for performance and scale testing",
        "cases": cases,
    }
    out.write_text(json.dumps(fixture, indent=2))
    print(f"Written {len(cases)} cases to {out}")


if __name__ == "__main__":
    main()
