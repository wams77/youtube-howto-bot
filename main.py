import os
import json
import requests
import google.generativeai as genai

# 1. SETUP API KEYS
# Mengambil API Key secara aman dari Environment Variables (GitHub Secrets)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")

# 2. FUNGSI GEMINI: MEMBUAT NASKAH SHORTS SEJARAH
def generate_history_short_script():
    print("[*] Meminta Gemini membuat naskah YouTube Short Sejarah...")
    if not GEMINI_KEY:
        print("[-] Error: GEMINI_API_KEY tidak ditemukan. Pastikan sudah diatur di GitHub Secrets!")
        return None
        
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Bertindaklah sebagai pembuat konten YouTube Shorts misteri/sejarah.
    Buatkan 1 fakta sejarah dunia yang sangat mengejutkan, aneh, atau jarang diketahui orang.
    
    ATURAN KETAT:
    - Naskah narasi (script_text) MAKSIMAL 80 kata agar durasinya pas di bawah 60 detik.
    - Harus sangat memancing rasa penasaran dari detik pertama.
    
    Hasilkan output HANYA dalam format JSON yang valid (tanpa markdown tambahan) dengan struktur:
    {
      "title": "Judul clickbait untuk metadata",
      "script_text": "Naskah narasi lengkap (Maks 80 kata)",
      "search_query_pexels": "1 kata kunci bahasa Inggris simbolis untuk video B-Roll (contoh: 'ancient ruins', 'vintage clock', 'scary forest', 'creepy statue')"
    }
    """
    
    try:
        response = model.generate_content(prompt)
        # Membersihkan output teks agar format JSON valid terbaca oleh Python
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        script_data = json.loads(raw_text)
        print(f"[+] Berhasil membuat naskah! Judul: {script_data['title']}")
        return script_data
    except Exception as e:
        print("[-] Gagal memproses data JSON dari Gemini:", e)
        return None

# 3. FUNGSI PEXELS: MENCARI DAN MENGUNDUH B-ROLL VERTIKAL
def download_vertical_broll(query, filename="background_shorts.mp4"):
    print(f"[*] Mencari video Shorts (vertikal) di Pexels untuk kata kunci: '{query}'...")
    if not PEXELS_KEY:
        print("[-] Error: PEXELS_API_KEY tidak ditemukan. Pastikan sudah diatur di GitHub Secrets!")
        return False
        
    headers = {"Authorization": PEXELS_KEY}
    # Parameter &orientation=portrait memastikan video yang diunduh berformat vertikal (9:16)
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get("videos"):
            # Mengambil data file video
            video_files = response["videos"][0]["video_files"]
            video_url = video_files[0]["link"]
            print(f"[+] Video vertikal ditemukan! Mulai mengunduh dari Pexels...")
            
            # Proses mengunduh dan menyimpan file video
            vid_data = requests.get(video_url)
            with open(filename, 'wb') as f:
                f.write(vid_data.content)
            print(f"[+] Video berhasil disimpan sebagai '{filename}'")
            return True
        else:
            print("[-] Video vertikal tidak ditemukan untuk kata kunci tersebut. Coba jalankan ulang.")
            return False
    except Exception as e:
        print("[-] Gagal menghubungi Pexels API:", e)
        return False

# 4. BLOK EKSEKUSI UTAMA (PIPELINE)
if __name__ == "__main__":
    print("=== BOT YOUTUBE SHORTS SEJARAH (Tahap 1) ===\n")
    
    # Langkah A: Meminta bot membuat Naskah & Ide
    script = generate_history_short_script()
    
    if script:
        # Menyimpan naskah ke file JSON agar bisa diunggah sebagai artifact di GitHub Actions
        with open("script_data.json", "w", encoding="utf-8") as f:
            json.dump(script, f, indent=4, ensure_ascii=False)
        print("[+] Naskah berhasil disimpan sebagai 'script_data.json'\n")
        
        # Langkah B: Mencari & Mengunduh Video B-Roll
        keyword = script['search_query_pexels']
        download_vertical_broll(keyword, "background_shorts.mp4")
        
        print("\n=== PROSES SELESAI ===")
        print("File 'script_data.json' dan 'background_shorts.mp4' siap dikemas oleh GitHub Actions!")
