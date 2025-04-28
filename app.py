import os
import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# Örnek Job sınıfı
class Job:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description or ""
        self.is_completed = False
        self.result = None

    def complete(self, result=None):
        self.is_completed = True
        self.result = result
        return self

    def __str__(self):
        status = "completed" if self.is_completed else "pending"
        return f"Job: {self.name} ({status})"


# LLM modeli ve entegrasyon ayarları
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")  # Varsayılan model


def generate_code_with_ollama(prompt, model=LLM_MODEL):
    """Ollama API'sini kullanarak yerel LLM ile kod ve başlık üretme"""
    ollama_url = f"{OLLAMA_HOST}/api/generate"

    system_prompt = """
    Sen bir Python kod üreticisisin. Sana verilen prompt'a göre Python kodu üretmelisin.
    Kodun bir Job sınıfını temel alarak çalışmalıdır. Job sınıfı şu özelliklere sahiptir:
    
    class Job:
        def __init__(self, name, description=None):
            self.name = name
            self.description = description or ""
            self.is_completed = False
            self.result = None
        
        def complete(self, result=None):
            self.is_completed = True
            self.result = result
            return self
        
        def __str__(self):
            status = "completed" if self.is_completed else "pending"
            return f"Job: {self.name} ({status})"
    
    Yanıtını şu formatta ver:
    BAŞLIK: [Kod için kısa ve açıklayıcı bir başlık]
    
    ```python
    [Üretilen Python kodu]
    ```
    
    Kodu kesinlikle Job sınıfını kullanan ve verilen prompt'a uygun şekilde oluştur.
    """

    full_prompt = f"{system_prompt}\n\nKullanıcı Prompt'u: {prompt}"

    # Ollama API isteği
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
    }

    try:
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()  # Hata kontrolü

        # API yanıtını işle
        result = response.json()
        generated_text = result.get("response", "")

        title = ""
        code = ""

        # "BAŞLIK:" ile başlayan metni bul
        if "BAŞLIK:" in generated_text:
            title_start = generated_text.find("BAŞLIK:")
            code_start = generated_text.find("```python", title_start)

            if title_start != -1 and code_start != -1:
                title = generated_text[title_start + 7 : code_start].strip()

                # Kod bloğunu çıkar
                code_end = generated_text.find("```", code_start + 9)
                if code_end != -1:
                    code = generated_text[code_start + 9 : code_end].strip()

        if not title or not code:
            # Basit bir fall-back ayrıştırma
            if "```python" in generated_text:
                code_start = generated_text.find("```python")
                code_end = generated_text.find("```", code_start + 9)
                if code_start != -1 and code_end != -1:
                    code = generated_text[code_start + 9 : code_end].strip()
                    title = "Oluşturulan Kod"

        return {
            "title": title,
            "code": code,
            "full_response": generated_text,
        }

    except Exception as e:
        return {
            "title": "Hata",
            "code": f"Kod üretilirken bir hata oluştu: {str(e)}",
            "full_response": str(e),
        }


@app.route("/")
def index():
    # Yüklü modelleri kontrol et
    try:
        models_url = f"{OLLAMA_HOST}/api/tags"
        models_response = requests.get(models_url)
        models_data = models_response.json()
        available_models = [model["name"] for model in models_data.get("models", [])]
    except Exception:
        available_models = [LLM_MODEL]

    return render_template("index.html", models=available_models)


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "")
    model = request.form.get("model", LLM_MODEL)

    if not prompt:
        return jsonify({"error": "Prompt boş olamaz"}), 400

    result = generate_code_with_ollama(prompt, model)

    return jsonify(result)


@app.route("/models", methods=["GET"])
def get_models():
    try:
        models_url = f"{OLLAMA_HOST}/api/tags"
        models_response = requests.get(models_url)
        models_data = models_response.json()
        available_models = [model["name"] for model in models_data.get("models", [])]
        return jsonify({"models": available_models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Ollama bağlantısını kontrol et
    try:
        health_check = requests.get(f"{OLLAMA_HOST}/api/tags")
        if health_check.status_code == 200:
            print(f"Ollama bağlantısı başarılı! Adres: {OLLAMA_HOST}")
            models = health_check.json().get("models", [])
            if models:
                print(f"Yüklü modeller: {', '.join([m['name'] for m in models])}")
            else:
                print(
                    "Henüz yüklü model yok. 'ollama pull llama3' ile model indirebilirsiniz."
                )
        else:
            print(
                f"Ollama bağlantı hatası! HTTP durum kodu: {health_check.status_code}"
            )
    except Exception as e:
        print(f"Ollama bağlantı hatası: {str(e)}")
        print("Ollama'nın kurulu ve çalışır durumda olduğundan emin olun!")

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="127.0.0.1", port=port)
