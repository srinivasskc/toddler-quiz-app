# Toddler Learning Buddy

A playful Streamlit quiz for young children. Choose a topic, answer simple questions, listen to them read aloud, and explore picture clues. Quiz questions are generated locally with Ollama and Gemma 2B.

## Set up Ollama and Gemma 2B

1. Install Ollama from [ollama.com/download](https://ollama.com/download) and start it.
2. In a terminal, download the model:

   ```powershell
   ollama pull gemma:2b
   ```

   If Ollama is not already running, start it in a separate terminal with `ollama serve`.

## Install and run the app

From the project folder, install the Python dependencies:

```powershell
pip install -r requirements.txt
```

Then start the app:

```powershell
streamlit run app.py
```

Streamlit will print a local URL to open in your browser. Keep Ollama running while using the app.
