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
                num_questions=min(int(num_questions), 8),  # Limit to 8 questions maximum
                custom_instructions=f"{custom_instructions}. Generate exactly {num_questions} questions.",  # Explicitly request the number of questions
            )
            
            # Verify questions are generated and match requested count
            if not ques or not ques.questions or len(ques.questions) != num_questions:
                st.error(f"Failed to generate {num_questions} questions. Please try again.")
                st.stop()
            
            # Display Questions
            st.header("Your Quiz")
            for idx, question in enumerate(ques.questions, 1):
                st.markdown(f"**Q{idx}: {question.question}**")
                for option in question.options:
                    st.markdown(f"- {option}")
                st.markdown(f"**Answer:** {question.answer}\n")
            
            # Calculate final latency
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
        
        # Update timer one last time with final time
        timer_placeholder.text(f"⏱️ Final Generation Time: {latency_ms/1000:.2f} seconds")
        
        # Display Latency
        st.success(f"Quiz generated in {latency_ms} ms!")
        
        # Save to Supabase with error handling
        with st.spinner("Saving your quiz to the database..."):
            try:
                # Insert into quizzes table
                quiz_data = {
                    "topic": topic,
                    "num_questions": num_questions,
                    "custom_instructions": custom_instructions,
                    "latency_ms": latency_ms,
                    "created_at": datetime.now().isoformat()  # Add explicit timestamp
                }
                
                # Retry logic for database connection
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        quiz_response = supabase.table("quizzes").insert(quiz_data).execute()
                        quiz_id = quiz_response.data[0]["id"]
                        
                        # Prepare questions data
                        questions_data = []
                        for question in ques.questions:
                            q = {
                                "quiz_id": quiz_id,
                                "question_text": question.question,
                                "options": json.dumps(question.options),
                                "answer": question.answer
                            }
                            questions_data.append(q)
                        
                        # Insert into questions table
                        supabase.table("questions").insert(questions_data).execute()
                        st.success("Your quiz has been saved successfully!")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            st.error(f"Failed to save to database after {max_retries} attempts. Your quiz was generated but couldn't be saved.")
                            st.error(f"Error: {str(e)}")
                        time.sleep(1)  # Wait 1 second before retrying
            
            except Exception as e:
                st.error("Failed to save quiz to database.")
                st.error(f"Error: {str(e)}")
                
    except Exception as e:
        st.error("Failed to generate quiz.")
        st.error(f"Error: {str(e)}")

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

# Footer
st.markdown("---")
st.markdown("© 2023 World's Fastest Quiz App. All rights reserved.")