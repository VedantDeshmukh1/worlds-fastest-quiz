# 🚀 World's Fastest Quiz App

The World's Fastest Quiz App is a lightning-fast quiz generation platform powered by Educhain and Cerebras LLaMA 3.1 70B. Generate comprehensive quizzes on any topic in seconds!

## ⚡ Features

- **Blazing Fast**: Generate quizzes in milliseconds using state-of-the-art LLM technology
- **Customizable**: Create quizzes with up to 50 questions
- **Topic Flexibility**: Generate questions on any subject matter
- **Real-time Stats**: Track generation times and quiz metrics
- **Persistent Storage**: All quizzes are automatically saved to Supabase
- **Custom Instructions**: Fine-tune your quiz content with specific requirements

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI Model**: Cerebras LLaMA 3.1 70B
- **Database**: Supabase
- **Framework**: Educhain
- **Language**: Python 3.x

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/worlds-fastest-quiz-app.git
cd worlds-fastest-quiz-app
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_supabase_key
CEREBRAS_API_KEY=your_cerebras_key
```

## 🚀 Usage

1. Start the app:
```bash
streamlit run streamlit_app.py
```

2. Configure your quiz:
   - Enter a topic
   - Set number of questions (1-50)
   - Add custom instructions
   - Click "Generate Quiz"

3. View your quiz and statistics

## 📊 Database Schema

### Quizzes Table
- id (UUID, primary key)
- topic (text)
- num_questions (integer)
- custom_instructions (text)
- latency_ms (integer)
- created_at (timestamp)

### Questions Table
- id (UUID, primary key)
- quiz_id (UUID, foreign key)
- question_text (text)
- options (json)
- answer (text)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Educhain](https://educhain.in
  ) for the powerful question generation engine
- [Cerebras](https://cerebras.ai) for the LLaMA 3.1 70B model access
- [Streamlit](https://streamlit.io) for the amazing web framework
- [Supabase](https://supabase.com) for the reliable database solution

---

Made with ❤️ by team educhain

