import os
import json
import requests
import subprocess
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import loop
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. SETUP API & SISTEM MEMORI (HISTORY)
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_TOKEN_JSON = os.environ.get("YOUTUBE_TOKEN")
HISTORY_FILE = "history.txt"

def load_history():
    """Membaca history.txt agar bot tahu apa yang sudah diposting."""
    if not os.path.exists(HISTORY_FILE):
        return {"titles": [], "videos": []}
    
    history_data = {"titles": [], "videos": []}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("[TITLE]"):
                history_data["titles"].append(line.replace("[TITLE]", "").strip())
            elif line.startswith("[VIDEO]"):
                history_data["videos"].append(line.replace("[VIDEO]", "").strip())
    return history_data

def save_history(title, video_id):
    """Menyimpan judul dan ID video yang baru dipakai ke history.txt."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[TITLE] {title}\n")
        f.write(f"[VIDEO] {video_id}\n")

# Load memory ke dalam variabel global
bot_history = load_history()

# ==========================================
# 2. FUNGSI GEMINI (ANTI-DUPLIKAT)
# ==========================================
def generate_history_short_script():
    print("[*] Meminta Gemini membuat naskah sejarah baru...")
    if not GEMINI_KEY:
        print("[-] Error: GEMINI_API_KEY tidak ditemukan!")
        return None
        
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Ambil 10 judul terakhir untuk memberi tahu AI agar tidak mengulangnya
    recent_titles = ", ".join(bot_history["titles"][-10:]) if bot_history["titles"] else "Belum ada"
    
    prompt = f"""
    Bertindaklah sebagai pencerita sejarah jenius dan stand-up komedian.
    Pilihlah 1 fakta sejarah dunia yang SANGAT UNIK, ANEH, ATAU BIKIN MERINDING. 
    
    PENTING! JANGAN MEMBAHAS TOPIK BERIKUT KARENA SUDAH PERNAH DIBUAT: {recent_titles}
    
    ATURAN KETAT UNTUK VIRALITAS & KOMEDI:
    1. "title": Buat judul clickbait jujur yang memancing rasa penasaran (maks 60 karakter).
    2. "script_text": Maksimal 70 kata. 
       - Kalimat pertama HARUS berupa "HOOK" kuat.
       - GAYA BAHASA: Asik, santai, kekinian, sisipkan candaan, sarkasme, atau lelucon receh di tengah cerita agar penonton tertawa. Hindari bahasa baku/kaku.
       - Kalimat terakhir HARUS memancing penonton berkomentar.
    
    Hasilkan output HANYA dalam format JSON valid dengan struktur:
    {{
      "title": "Judul clickbait viral",
      "script_text": "Naskah narasi lengkap dengan hook, candaan, dan pancingan komentar",
      "search_query_pexels": "abaikan ini"
    }}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        script_data = json.loads(raw_text)
        print(f"[+] Berhasil membuat naskah! Judul: {script_data['title']}")
        return script_data
    except Exception as e:
        print("[-] Gagal memproses data JSON dari Gemini:", e)
        return None

# ==========================================
# 3. FUNGSI PEXELS (ACAK HALAMAN & ANTI-DUPLIKAT)
# ==========================================
def download_vertical_broll(query, filename="background_shorts.mp4"):
    print(f"[*] Mencari video di Pexels: '{query}'...")
    if not PEXELS_KEY:
        print("[-] Error: PEXELS_API_KEY tidak ditemukan!")
        return None
        
    headers = {"Authorization": PEXELS_KEY}
    
    # Mengacak halaman dari 1 sampai 10 agar videonya tidak itu-itu saja
    random_page = random.randint(1, 10)
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&page={random_page}&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get("videos"):
            for video in response["videos"]:
                video_id = str(video["id"])
                
                # Cek apakah video ini sudah pernah dipakai di history
                if video_id in bot_history["videos"]:
                    continue # Kalo sudah, lewati dan cari video berikutnya
                
                video_url = video["video_files"][0]["link"]
                print(f"[+] Mengunduh video Pexels ID: {video_id}...")
                vid_data = requests.get(video_url)
                with open(filename, 'wb') as f:
                    f.write(vid_data.content)
                print(f"[+] Video disimpan: '{filename}'")
                return video_id # Mengembalikan ID video untuk disimpan
                
            print("[-] Semua video di halaman ini sudah pernah dipakai.")
            return None
        else:
            print("[-] Video tidak ditemukan.")
            return None
    except Exception as e:
        print("[-] Gagal menghubungi Pexels API:", e)
        return None

# ==========================================
# 4. FUNGSI EDGE-TTS
# ==========================================
def generate_voiceover(text, filename="voiceover.mp3"):
    print("[*] Menghasilkan suara AI...")
    voice = "id-ID-ArdiNeural"
    safe_text = text.replace('"', '').replace("'", "")
    
    command = f'edge-tts --voice {voice} --text "{safe_text}" --write-media {filename}'
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except Exception as e:
        print("[-] Gagal menghasilkan suara:", e)
        return False

# ==========================================
# 5. FUNGSI MOVIEPY
# ==========================================
def edit_video_with_captions(video_file, audio_file, script_text, output_file="final_shorts.mp4"):
    print("[*] Merender video dengan subtitle...")
    try:
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)
        
        if video.duration < audio.duration:
            video = video.fx(loop, duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
            
        video = video.set_audio(audio)
        
        words = script_text.split(" ")
        chunks = []
        chunk_size = 3  
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
            
        total_duration = audio.duration
        total_chars = sum(len(c) for c in chunks)
        font_path = "Montserrat-Black.ttf"
        text_clips = []
        current_time = 0.0
        
        for text in chunks:
            chunk_duration = (len(text) / total_chars) * total_duration if total_chars > 0 else total_duration / len(chunks)
            chunk_duration = max(chunk_duration, 0.6) 
            
            txt_clip = TextClip(
                text, 
                fontsize=50, 
                color='yellow', 
                font=font_path, 
                stroke_color='black', 
                stroke_width=3,
                size=(video.w - 80, None), 
                method='caption'
            )
            
            txt_clip = txt_clip.set_start(current_time)
            txt_clip = txt_clip.set_duration(chunk_duration)
            txt_clip = txt_clip.set_position(('center', 'center'))
            text_clips.append(txt_clip)
            current_time += chunk_duration
            
        final_video = CompositeVideoClip([video] + text_clips)
        final_video.write_videofile(
            output_file, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", logger=None
        )
        return True
    except Exception as e:
        print("[-] Gagal mengedit video:", e)
        return False

# ==========================================
# 6. FUNGSI YOUTUBE
# ==========================================
def upload_to_youtube(video_file, title, description):
    print("[*] Uploading ke YouTube...")
    if not YOUTUBE_TOKEN_JSON:
        return False
        
    try:
        token_data = json.loads(YOUTUBE_TOKEN_JSON)
        creds = Credentials.from_authorized_user_info(token_data)
        youtube = build('youtube', 'v3', credentials=creds)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['shorts', 'sejarah', 'faktaunik', 'misteri', 'funnyanimals', 'komedi', 'trending', 'lucu'],
                'categoryId': '24' 
            },
            'status': {
                'privacyStatus': 'public', 
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = request.execute()
        print(f"[+] Video Berhasil Diupload! Link: https://youtu.be/{response['id']}")
        return True
    except Exception as e:
        print("[-] Gagal upload:", e)
        return False

# ==========================================
# 7. BLOK EKSEKUSI UTAMA
# ==========================================
if __name__ == "__main__":
    print("=== BOT YOUTUBE SHORTS (MEMORY ENABLED) ===\n")
    
    script = generate_history_short_script()
    
    if script:
        keyword = "funny animal"
        narasi_bersih = script['script_text'].replace('*', '').replace('\n', ' ').strip()
        judul = script['title']
        deskripsi = f"{judul}\n\nFakta sejarah dunia paling aneh!\nMenurut kalian gimana? Coba komen di bawah!\nJangan lupa LIKE & SUBSCRIBE!\n#shorts #sejarah #faktaunik #funnyanimals #komedi"
        
        # Pexels sekarang akan mengembalikan ID video
        video_id_dipakai = download_vertical_broll(keyword, "background_shorts.mp4")
        voice_success = generate_voiceover(narasi_bersih, "voiceover.mp3")
        
        if video_id_dipakai and voice_success:
            edit_success = edit_video_with_captions("background_shorts.mp4", "voiceover.mp3", narasi_bersih, "final_shorts.mp4")
            
            if edit_success:
                upload_success = upload_to_youtube("final_shorts.mp4", judul, deskripsi)
                
                if upload_success:
                    # Simpan data ke memori HANYA jika upload sukses
                    save_history(judul, video_id_dipakai)
                    print("[+] Data berhasil dicatat ke history.txt")
                    
        print("\n=== SELURUH PROSES SELESAI ===")
