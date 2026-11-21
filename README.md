# Interview Practice Bot (PS18)

**Name:** Ketan Singh | **Roll No:** 18 | **Class:** AIA4

## Problem Statement
Students lack mock interview practice. This bot asks role-based interview questions one at a time and gives a score and feedback on each answer, followed by a final summary.

## How It Works
1. User enters a role and level.
2. The LLM generates 5 interview questions.
3. Questions are asked one at a time.
4. Each answer is sent to the LLM for a score (out of 10) and feedback.
5. A final summary shows the average score, strengths and areas to improve.

## Tech Stack
- Python
- Streamlit (UI)
- Groq API with openai/gpt-oss-120b

## How to Run
1. Install the libraries:
   pip install -r requirements.txt
2. Create a `.env` file in the project folder containing:
   GROQ_API_KEY=your_key_here
   (Get a free key at console.groq.com)
3. Start the app:
   streamlit run app.py

## Screenshots
Data%20analyst%20question%202.png
![Screenshot 2](Data analyst question 2.png)
