from agent import decompose_question

TEST_QUESTIONS = {
    "WATO (single-topic, should stay one sub-question)":
        "What is the WATO tax offset amount?",
    "Discretionary trust (compound, should decompose)":
        "Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?",
    "Tax planning (compound + advice-framed, should decompose into factual sub-questions)":
        "What is the best way to plan my finances to reduce my tax, including for a working couple with kids?",
}

for label, question in TEST_QUESTIONS.items():
    print(f"--- {label} ---")
    print(f"Original: {question}")
    sub_questions = decompose_question(question)
    print(f"Decomposed into {len(sub_questions)} sub-question(s):")
    for i, sq in enumerate(sub_questions, start=1):
        print(f"  {i}. {sq}")
    print()