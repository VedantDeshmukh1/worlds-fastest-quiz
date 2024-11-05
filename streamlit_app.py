import os
import time
import json
import streamlit as st
from supabase import create_client, Client
from langchain_openai import ChatOpenAI
from educhain import Educhain
from educhain.core.config import LLMConfig
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Initialize Educhain with ChatOpenAI
llama3_70b = ChatOpenAI(
    model="llama3.1-70b",
    openai_api_base="https://api.cerebras.ai/v1",
    openai_api_key=CEREBRAS_API_KEY
)
llama3_70b_config = LLMConfig(custom_model=llama3_70b)
client = Educhain(llama3_70b_config)

# Streamlit App Title
st.set_page_config(page_title="World's Fastest Quiz App", page_icon="🚀")
st.title("🚀 World's Fastest Quiz App")

# Sidebar for User Inputs
st.sidebar.header("Configure Your Quiz")

# Input Fields
topic = st.sidebar.text_input("Quiz Topic", value="Psychology")
num_questions = st.sidebar.number_input("Number of Questions", min_value=1, max_value=50, value=10, step=1)
custom_instructions = st.sidebar.text_area("Custom Instructions", value="Classical Conditioning")

# Add this near the top with other imports
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
    st.session_state.questions = None
    st.session_state.user_answers = {}
    st.session_state.submitted = False

# Button to Generate Quiz
if st.sidebar.button("Generate Quiz"):
    try:
        # Create a placeholder for the timer
        timer_placeholder = st.empty()
        start_time = time.time()
        
        # Create a progress indicator
        with st.spinner("Generating your quiz..."):
            # Generate Questions
            ques = client.qna_engine.generate_questions(
                topic=topic,
                num_questions=min(int(num_questions), 8),
                custom_instructions=f"{custom_instructions}. Generate exactly {num_questions} questions.",
            )
            
            # Verify questions are generated and match requested count
            if not ques or not ques.questions or len(ques.questions) != num_questions:
                st.error(f"Failed to generate {num_questions} questions. Please try again.")
                st.stop()
            
            # Store in session state
            st.session_state.questions = ques.questions
            st.session_state.quiz_generated = True
            
            # Calculate final latency
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Save to Supabase with error handling
            with st.spinner("Saving your quiz to the database..."):
                try:
                    # Insert into quizzes table
                    quiz_data = {
                        "topic": topic,
                        "num_questions": num_questions,
                        "custom_instructions": custom_instructions,
                        "latency_ms": latency_ms,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Retry logic for database connection
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            supabase.table("quizzes").insert(quiz_data).execute()
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:  # Last attempt
                                st.warning("Failed to save to database after 3 attempts. Your quiz was generated but couldn't be saved.")
                                st.error(f"Error: {str(e)}")
                            time.sleep(1)  # Wait before retry
                            
                except Exception as e:
                    st.warning("Failed to save quiz to database. Your quiz was generated but couldn't be saved.")
                    st.error(f"Error: {str(e)}")
            
            # Update timer and show latency
            timer_placeholder.text(f"⏱️ Final Generation Time: {latency_ms/1000:.2f} seconds")
            st.success(f"Quiz generated in {latency_ms} ms!")
            
    except Exception as e:
        st.error("Failed to generate quiz.")
        st.error(f"Error: {str(e)}")

# Display quiz if it's generated (SINGLE INSTANCE)
if st.session_state.quiz_generated:
    st.header("Your Quiz")
    
    for idx, question in enumerate(st.session_state.questions, 1):
        st.markdown(f"**Q{idx}: {question.question}**")
        options = question.options
        answer_key = f"q_{idx}"
        
        # Initialize answer in session state if not present
        if answer_key not in st.session_state.user_answers:
            st.session_state.user_answers[answer_key] = None
            
        # Display radio buttons with an initial empty option
        st.session_state.user_answers[answer_key] = st.radio(
            f"Select your answer for question {idx}:",
            ["Select an option..."] + options,  # Add initial empty option
            key=f"quiz_answer_{idx}"
        )
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Submit button
    if st.button("Submit Quiz", key="submit_button"):
        # Check if all questions are answered
        unanswered = [idx for idx, ans in st.session_state.user_answers.items() 
                     if ans == "Select an option..."]
        
        if unanswered:
            st.error(f"Please answer all questions before submitting! Unanswered questions: {', '.join(str(q[2]) for q in unanswered)}")
        else:
            st.session_state.submitted = True
    
    # Show results after submission
    if st.session_state.submitted:
        st.header("Quiz Results")
        correct_count = 0
        
        for idx, question in enumerate(st.session_state.questions, 1):
            st.markdown(f"**Q{idx}: {question.question}**")
            user_answer = st.session_state.user_answers[f"q_{idx}"]
            correct_answer = question.answer
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_count += 1
                st.markdown(f"✅ Your answer: **{user_answer}** (Correct!)")
            else:
                st.markdown(f"❌ Your answer: **{user_answer}**")
                st.markdown(f"📝 Correct answer: **{correct_answer}**")
            st.markdown("---")
        
        score_percentage = (correct_count / len(st.session_state.questions)) * 100
        st.success(f"Final Score: {correct_count}/{len(st.session_state.questions)} ({score_percentage:.1f}%)")

        if st.button("Take Another Quiz", key="retry_button"):
            st.session_state.quiz_generated = False
            st.session_state.questions = None
            st.session_state.user_answers = {}
            st.session_state.submitted = False
            st.experimental_rerun()

# Replace Previous Quizzes section with Metrics
st.header("📊 Quiz Generation Stats")

try:
    # Fetch quiz statistics
    stats = supabase.table("quizzes").select("latency_ms").execute().data
    
    if stats:
        avg_latency = sum(q['latency_ms'] for q in stats) / len(stats)
        total_quizzes = len(stats)
        
        # Display metrics in columns
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Generation Time", f"{avg_latency/1000:.2f} seconds")
        with col2:
            st.metric("Total Quizzes Generated", total_quizzes)
except Exception as e:
    st.error("Failed to load quiz statistics.")
    st.error(f"Error: {str(e)}")

# Footer with credits
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>© 2024 World's Fastest Quiz App. All rights reserved.</p>
    <p>Powered by <a href='https://educhain.in' target='_blank'>Educhain</a> 🎓🔗</p>
    <p>Made with ❤️ using <a href='https://github.com/satvik314/educhain.git' target='_blank'>Educhain</a> - A Python package for generating educational content using Generative AI</p>
</div>
""", unsafe_allow_html=True)
