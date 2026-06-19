# app/utils.py
from app.config import USE_OLLAMA, OLLAMA_MODEL, HF_MODEL

def get_llm():
    if USE_OLLAMA:
        import ollama
        class OllamaLLM:
            def __call__(self, prompt, system=None):
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=messages
                )
                return response["message"]["content"]
        return OllamaLLM()
    else:
        from transformers import pipeline
        pipe = pipeline("text-generation", model=HF_MODEL, device_map="auto")
        class HFLLM:
            def __call__(self, prompt, system=None):
                # For HF, we ignore system and just use prompt
                result = pipe(prompt, max_new_tokens=512, do_sample=False)[0]["generated_text"]
                return result[len(prompt):].strip()
        return HFLLM()