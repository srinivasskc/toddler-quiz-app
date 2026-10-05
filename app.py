import html
import json
import random
import re
from io import BytesIO

import ollama
import streamlit as st
from gtts import gTTS
from gtts.tts import gTTSError


st.set_page_config(page_title="Toddler Learning Buddy", page_icon="🎈")
st.title("🎈 Toddler Learning Buddy")
st.write("A playful learning quiz for little learners. Pick a topic and let's play!")

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fff8e8 0%, #f1f8ff 100%); }
    div.stButton > button { min-height: 3rem; border-radius: 1rem; font-size: 1.05rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def generate_question(category):
    if "counting" in category.casefold():
        items = {
            "apples": "🍎",
            "bananas": "🍌",
            "stars": "⭐",
            "balls": "⚽",
            "ducks": "🦆",
        }
        previous_item = st.session_state.get("last_counting_item")
        pairs = [
            (item, count)
            for item in items
            for count in range(1, 11)
            if item != previous_item
        ]
        visual_item, visual_count = random.choice(pairs)
        st.session_state["last_counting_item"] = visual_item

        question_templates = [
            "How many {item} are shown?",
            "Can you count the {item}?",
            "How many {item} can you see?",
            "Let's count! How many {item} are there?",
        ]
        answer_choices = {visual_count}
        while len(answer_choices) < 3:
            answer_choices.add(random.randint(1, 10))

        return {
            "question": random.choice(question_templates).format(item=visual_item),
            "choices": [str(number) for number in random.sample(list(answer_choices), 3)],
            "answer": str(visual_count),
            "visual_item": visual_item,
            "visual_count": visual_count,
        }

    prompt = f"""
    You are a gentle, enthusiastic preschool teacher.
    Create one very short, fun multiple-choice question for a 3-year-old about {category}.
    Keep the question under 12 words. Give exactly 3 simple answer choices and exactly
    one correct answer. Use familiar, child-friendly words.
    Return only a JSON object with exactly these fields:
    {{"question": "question text", "choices": ["choice 1", "choice 2", "choice 3"], "answer": "copy the correct choice exactly"}}
    """
    for attempt in range(3):
        response = ollama.chat(
            model="gemma:2b",
            format="json",
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            quiz = json.loads(response["message"]["content"])
        except (json.JSONDecodeError, KeyError, TypeError):
            quiz = None

        if isinstance(quiz, dict):
            question = quiz.get("question")
            choices = quiz.get("choices")
            answer = quiz.get("answer")
            if (
                isinstance(question, str)
                and question.strip()
                and isinstance(choices, list)
                and len(choices) == 3
                and all(isinstance(choice, str) and choice.strip() for choice in choices)
                and len({choice.strip().casefold() for choice in choices}) == 3
                and isinstance(answer, str)
            ):
                choices = [choice.strip() for choice in choices]
                answer_key = re.sub(r"[^a-z0-9]", "", answer.casefold())
                correct_choice = next(
                    (
                        choice
                        for choice in choices
                        if re.sub(r"[^a-z0-9]", "", choice.casefold()) == answer_key
                    ),
                    None,
                )
                if correct_choice:
                    return {
                        "question": question.strip(),
                        "choices": choices,
                        "answer": correct_choice,
                    }

        prompt += """

Your previous response was invalid. Try again and follow the JSON format exactly.
The answer must exactly match one of the three choices. Return no extra text.
"""

    raise ValueError(
        "I couldn't get a complete question after a few tries. Please ask again."
    )


def text_to_speech(text):
    audio = BytesIO()
    gTTS(text=text, lang="en").write_to_fp(audio)
    return audio.getvalue()


def spoken_quiz_text(quiz):
    spoken_choices = ", ".join(quiz["choices"][:-1])
    spoken_choices += f", or {quiz['choices'][-1]}"
    return f"{quiz['question']} You can choose {spoken_choices}."


def choice_illustration(choice, category):
    choice_text = choice.casefold()
    illustrations = {
        "cow": "🐮", "dog": "🐶", "cat": "🐱", "duck": "🦆",
        "sheep": "🐑", "pig": "🐷", "horse": "🐴", "bird": "🐦",
        "lion": "🦁", "elephant": "🐘", "monkey": "🐵", "frog": "🐸",
        "red": "🔴", "orange": "🟠", "yellow": "🟡", "green": "🟢",
        "blue": "🔵", "purple": "🟣", "pink": "🩷", "black": "⚫",
        "white": "⚪", "brown": "🟤", "circle": "🔵", "square": "🟦",
        "triangle": "🔺", "star": "⭐", "heart": "❤️", "rectangle": "🟪",
        "one": "1️⃣", "two": "2️⃣", "three": "3️⃣", "four": "4️⃣",
        "five": "5️⃣", "six": "6️⃣", "seven": "7️⃣", "eight": "8️⃣",
        "nine": "9️⃣", "ten": "🔟", "1": "1️⃣", "2": "2️⃣",
        "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣",
        "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "10": "🔟",
    }
    for word, illustration in illustrations.items():
        if re.search(rf"\b{re.escape(word)}\b", choice_text):
            return illustration
    if "animal" in category.casefold():
        return "🐾"
    if "color" in category.casefold() or "shape" in category.casefold():
        return "🎨"
    return "🍎"


st.session_state.setdefault("score", 0)
st.session_state.setdefault("answered_count", 0)
st.session_state.setdefault("current_quiz", None)
st.session_state.setdefault("answer_submitted", False)
st.session_state.setdefault("audio_bytes", None)

category = st.radio(
    "Choose a topic:",
    ["Animal Sounds 🐶", "Colors & Shapes 🎨", "Counting 🍎"],
    horizontal=True,
)

score_col, rounds_col = st.columns(2)
score_col.metric("⭐ Stars", st.session_state["score"])
rounds_col.metric("🎯 Questions tried", st.session_state["answered_count"])

if st.button(
    "✨ Ask a New Question! ✨",
    type="primary",
    use_container_width=True,
):
    try:
        with st.spinner("Your learning buddy is thinking..."):
            quiz = generate_question(category)
        st.session_state["current_quiz"] = quiz
        st.session_state["answer_submitted"] = False
        st.session_state["answer_choice"] = None
        try:
            st.session_state["audio_bytes"] = text_to_speech(spoken_quiz_text(quiz))
        except gTTSError:
            st.session_state["audio_bytes"] = None
            st.warning("Your question is ready, but its audio couldn't be made.")
    except (ollama.RequestError, ollama.ResponseError) as error:
        st.error(
            "I couldn't reach the learning buddy. Check that Ollama is running "
            "and the gemma:2b model is available, then try again."
        )
        st.exception(error)
    except ValueError as error:
        st.error(str(error))

quiz = st.session_state["current_quiz"]
if quiz:
    st.divider()
    st.subheader(quiz["question"])

    if "visual_count" in quiz:
        st.caption("🖼️ Count the objects in the picture")
        object_emoji = {
            "apples": "🍎",
            "bananas": "🍌",
            "stars": "⭐",
            "balls": "⚽",
            "ducks": "🦆",
        }[quiz["visual_item"]]
        st.markdown(
            f"<div style='font-size:3rem; text-align:center; padding:12px;'>"
            f"{' '.join([object_emoji] * quiz['visual_count'])}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("🖼️ Picture clues")
        picture_columns = st.columns(len(quiz["choices"]))
        for column, choice in zip(picture_columns, quiz["choices"]):
            illustration = choice_illustration(choice, category)
            safe_choice = html.escape(choice)
            column.markdown(
                f"""
                <div style="background:#ffffffcc; border:2px solid #dceafa;
                            border-radius:16px; padding:12px 6px; text-align:center;">
                    <div style="font-size:3rem; line-height:1.2;">{illustration}</div>
                    <div style="font-size:1rem; font-weight:600;">{safe_choice}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.session_state["audio_bytes"]:
        st.audio(st.session_state["audio_bytes"], format="audio/mp3")

    st.write("### Tap the answer that you think is right:")
    st.radio(
        "Answer choices",
        quiz["choices"],
        index=None,
        horizontal=True,
        key="answer_choice",
        format_func=lambda choice: f"{choice_illustration(choice, category)} {choice}",
        label_visibility="collapsed",
        disabled=st.session_state["answer_submitted"],
    )

    if not st.session_state["answer_submitted"]:
        if st.button(
            "💡 Check my answer",
            disabled=not st.session_state.get("answer_choice"),
        ):
            st.session_state["answer_submitted"] = True
            st.session_state["answered_count"] += 1
            if st.session_state["answer_choice"].casefold() == quiz["answer"].casefold():
                st.session_state["score"] += 1
            st.rerun()
    elif st.session_state["answer_choice"].casefold() == quiz["answer"].casefold():
        st.balloons()
        st.success("🎉 That's right! You did a wonderful job!")
    else:
        st.info(f"🌟 Nice try! The answer is **{quiz['answer']}**. Let's keep learning!")

    if st.session_state["answer_submitted"]:
        st.caption("Ready for another one? Tap “Ask a New Question!” above.")
