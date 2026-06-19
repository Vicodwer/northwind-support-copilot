from app.config import USE_OLLAMA, OLLAMA_MODEL, HF_MODEL

def get_llm():
    if USE_OLLAMA:
        import ollama
        class OllamaLLM:
            def __call__(self, prompt):
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response["message"]["content"]
        return OllamaLLM()
    else:
        # HuggingFace pipeline - using a small instruct model
        from transformers import pipeline
        # Using flan-t5-large (good for instructions, ~1GB) 
        # Change to "google/flan-t5-xl" if you have RAM, or "gpt2" just to test flow.
        model_name = HF_MODEL if HF_MODEL else "google/flan-t5-large"
        print(f"Loading HF model: {model_name}... (this may take a minute)")
        pipe = pipeline(
            "text2text-generation",  # flan-t5 uses text2text
            model=model_name,
            device_map="auto",
            max_length=512
        )
        class HFLLM:
            def __call__(self, prompt):
                # flan-t5 works well with instruction prompts
                # We need to trim the prompt to avoid token limits
                # For flan, we ask a direct question.
                result = pipe(prompt, max_new_tokens=256, do_sample=False)[0]["generated_text"]
                return result.strip()
        return HFLLM()