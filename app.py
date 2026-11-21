import json
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"
NUM_QUESTIONS = 5


def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """Send a prompt to the LLM and return the parsed JSON reply."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def generate_questions(role: str, level: str) -> list[str]:
    system = "You are an expert interviewer. Reply ONLY with valid JSON."
    user = (
        f"Create {NUM_QUESTIONS} interview questions for a {level} {role} position. "
        "Mix technical and behavioural questions, ordered easy to hard. "
        'Return JSON: {"questions": ["q1", "q2", ...]}'
    )
    return call_llm(system, user)["questions"][:NUM_QUESTIONS]


def evaluate_answer(role: str, question: str, answer: str) -> dict:
    system = (
        "You are a strict but supportive interview coach. "
        "Score fairly: 1-3 weak, 4-6 average, 7-8 good, 9-10 excellent. "
        "Reply ONLY with valid JSON."
    )
    user = (
        f"Role: {role}\nQuestion: {question}\nCandidate answer: {answer}\n\n"
        'Return JSON: {"score": <integer 1-10>, "strengths": "<1-2 sentences>", '
        '"improvements": "<1-2 sentences>", "better_answer": "<short ideal answer>"}'
    )
    return call_llm(system, user)


def final_summary(role: str, results: list[dict]) -> dict:
    system = "You are an interview coach. Reply ONLY with valid JSON."
    transcript = "\n".join(
        f"Q{i+1}: {r['question']}\nScore: {r['score']}/10\nImprove: {r['improvements']}"
        for i, r in enumerate(results)
    )
    user = (
        f"Role: {role}\nInterview results:\n{transcript}\n\n"
        'Return JSON: {"summary": "<3 sentences>", "top_strengths": ["..",".."], '
        '"focus_areas": ["..",".."]}'
    )
    return call_llm(system, user)


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Interview Practice Bot", page_icon="🎤")
st.title("🎤 Interview Practice Bot")

ss = st.session_state
ss.setdefault("stage", "setup")  # setup -> interview -> done
ss.setdefault("questions", [])
ss.setdefault("idx", 0)
ss.setdefault("results", [])
ss.setdefault("role", "")

if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY not found. Add it to a .env file.")
    st.stop()

# --- Stage 1: pick role ---
if ss.stage == "setup":
    role = st.text_input("Role you're interviewing for", placeholder="e.g. Data Analyst")
    level = st.selectbox("Level", ["Fresher", "Junior", "Mid-level", "Senior"])
    if st.button("Start interview", disabled=not role.strip()):
        with st.spinner("Preparing questions..."):
            try:
                ss.questions = generate_questions(role.strip(), level)
                ss.role = role.strip()
                ss.idx, ss.results, ss.stage = 0, [], "interview"
                st.rerun()
            except Exception as e:
                st.error(f"Could not generate questions: {e}")

# --- Stage 2: ask one by one ---
elif ss.stage == "interview":
    i = ss.idx
    st.progress(i / len(ss.questions), text=f"Question {i+1} of {len(ss.questions)}")
    st.subheader(ss.questions[i])

    # show feedback of the just-answered question if any
    with st.form(key=f"form_{i}", clear_on_submit=True):
        answer = st.text_area("Your answer", height=150)
        submitted = st.form_submit_button("Submit answer")

    if submitted:
        if not answer.strip():
            st.warning("Please type an answer first.")
        else:
            with st.spinner("Evaluating..."):
                try:
                    fb = evaluate_answer(ss.role, ss.questions[i], answer)
                    fb["question"], fb["answer"] = ss.questions[i], answer
                    ss.results.append(fb)
                    ss.stage = "feedback"
                    st.rerun()
                except Exception as e:
                    st.error(f"Evaluation failed, try again: {e}")

# --- Stage 2b: show feedback for the answer ---
elif ss.stage == "feedback":
    r = ss.results[-1]
    st.subheader(r["question"])
    st.metric("Score", f"{r['score']}/10")
    st.success(f"**Strengths:** {r['strengths']}")
    st.warning(f"**Improve:** {r['improvements']}")
    with st.expander("See a stronger answer"):
        st.write(r["better_answer"])

    last = ss.idx == len(ss.questions) - 1
    if st.button("Finish & see summary" if last else "Next question"):
        if last:
            ss.stage = "done"
        else:
            ss.idx += 1
            ss.stage = "interview"
        st.rerun()

# --- Stage 3: final summary ---
elif ss.stage == "done":
    avg = sum(r["score"] for r in ss.results) / len(ss.results)
    st.header("Final summary")
    st.metric("Average score", f"{avg:.1f}/10")
    if "summary" not in ss:
        with st.spinner("Writing summary..."):
            try:
                ss.summary = final_summary(ss.role, ss.results)
            except Exception as e:
                ss.summary = {"summary": f"Summary unavailable: {e}",
                              "top_strengths": [], "focus_areas": []}
    s = ss.summary
    st.write(s["summary"])
    st.markdown("**Top strengths**")
    for x in s["top_strengths"]:
        st.markdown(f"- {x}")
    st.markdown("**Focus areas**")
    for x in s["focus_areas"]:
        st.markdown(f"- {x}")

    with st.expander("Question-by-question breakdown"):
        for n, r in enumerate(ss.results, 1):
            st.markdown(f"**Q{n}. {r['question']}** — {r['score']}/10")
            st.caption(r["improvements"])

    if st.button("Practice again"):
        for k in ["stage", "questions", "idx", "results", "role", "summary"]:
            ss.pop(k, None)
        st.rerun()
