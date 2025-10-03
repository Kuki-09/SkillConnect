# 🎯 Smart Internship/Project Matcher

AI-powered platform that matches students with internship and project opportunities using Azure cloud services and advanced NLP.

## 🚀 Overview

Students upload resumes to get personalized opportunity matches, while faculty/recruiters can post openings. The system uses Azure AI services to analyze resumes and generate intelligent matches with AI generated suggestions to improve the score.  
**Sample resumes are trained using a custom model through Azure Document Processing for accurate extraction.**

## 🛠️ Tech Stack

### Azure Services
- Azure Document Intelligence: Extracts structured data from PDF resumes
- Azure Text Analytics: Named entity recognition for skills identification

### AI/ML
- Sentence Transformers: Semantic similarity matching (all-MiniLM-L6-v2)
- spaCy: NLP processing and entity validation
- Ollama (Llama 3.2): Personalized recommendations to improve score
- LangChain: LLM orchestration

### Framework
- Streamlit
- Python

## ⚙️ Core Components

1. **form_recognizer.py**: Azure Document Intelligence integration for resume parsing  
2. **entity_extractor.py**: Azure Text Analytics + skill normalization  
3. **smart_matcher.py**: Semantic similarity scoring (60% exact + 30% fuzzy + 10% certifications)  
4. **suggestion_generator.py**: Ollama LLM integration for personalized recommendations to improve score  

## 🔧 Setup

### Prerequisites
- Python 3.8+  
- Azure subscription (Document Intelligence + Text Analytics)  
- Ollama with Llama 3.2  

### Installation

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
