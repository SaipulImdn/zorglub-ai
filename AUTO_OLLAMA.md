# 🤖 Zorglub AI - Auto-Start Ollama Feature

## ✨ New Feature: Auto-Start Ollama

Sekarang ketika menjalankan `python app.py`, aplikasi akan otomatis:
1. Mengambil model name dari `OLLAMA_MODEL` environment variable
2. Menjalankan `ollama run <model>` secara otomatis
3. Menunggu model untuk dimuat sebelum melanjutkan

## 🚀 Penggunaan

### Default Model (mistral):
```bash
source venv/bin/activate
python app.py --check
```

### Custom Model via Environment Variable:
```bash
source venv/bin/activate
OLLAMA_MODEL=deepseek-r1 python app.py --text
OLLAMA_MODEL=llama3.2 python app.py --voice
```

### Menggunakan Script Helper:
```bash
./run_with_model.sh mistral --check
./run_with_model.sh deepseek-r1 --text  
./run_with_model.sh llama3.2 --voice
```

## ⚙️ Konfigurasi Model

Edit environment variable atau ubah default di `shared/config.py`:
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # Default model
```

## 📋 Supported Models

Semua model yang tersedia di Ollama:
- `mistral` (default, lightweight)
- `deepseek-r1` (reasoning model)
- `llama3.2` (Meta's latest)
- `qwen2.5` (Alibaba's model)
- `codellama` (code generation)
- dll...

## 🔧 Auto-Start Features

✅ **Deteksi Model**: Cek apakah model sudah berjalan  
✅ **Auto Load**: Jalankan `ollama run <model>` jika belum  
✅ **Status Check**: Validasi model berhasil dimuat  
✅ **Error Handling**: Graceful fallback jika ada masalah  
✅ **Custom Model**: Support environment variable  

## 📖 Command Examples

```bash
# Test dengan berbagai model
python app.py --check                                    # mistral (default)
OLLAMA_MODEL=deepseek-r1 python app.py --check          # deepseek-r1
OLLAMA_MODEL=llama3.2 python app.py --text              # llama3.2

# Voice chat dengan model spesifik
./run_with_model.sh deepseek-r1 --voice                 # Voice chat + deepseek-r1
./run_with_model.sh codellama --text                    # Text chat + codellama
```

Sekarang tidak perlu manual `ollama run model` lagi! 🎉
