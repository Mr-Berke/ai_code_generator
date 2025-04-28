# AI Code Generator

Bu proje, Ollama LLM kullanarak Python kodu üreten bir web uygulamasıdır.

## Özellikler

- Ollama LLM entegrasyonu
- Flask web arayüzü
- Gunicorn ile production-ready deployment
- Docker desteği

## Kurulum

### Docker ile Çalıştırma

```bash
docker pull berketopbas/ai-code-generator
docker run -p 5000:5000 berketopbas/ai-code-generator
```

### Docker Compose ile Çalıştırma

```bash
docker-compose up
```

## Gereksinimler

- Python 3.12
- Ollama LLM
- Docker (opsiyonel)

## Ortam Değişkenleri

- `OLLAMA_HOST`: Ollama servisinin adresi (varsayılan: http://localhost:11434)
- `LLM_MODEL`: Kullanılacak LLM modeli (varsayılan: llama3)

## Lisans

MIT
