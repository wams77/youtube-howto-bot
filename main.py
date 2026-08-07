import os
import json
import requests
import subprocess
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import loop
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. SETUP API KEYS & SECRETS
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_TOKEN_JSON = os.environ.get("YOUTUBE_TOKEN")

# ==========================================
# 2. FUNGSI GEMINI (FORMULA VIRAL & BUMBU KOMEDI)
# ==========================================
def generate_history_short_script():
    print("[*] Meminta Gemini membuat naskah sejarah komedi...")
    if not GEMINI_KEY:
        print("[-] Error: GEMINI_API_KEY tidak ditemukan!")
        return None
        
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = """
    Bertindaklah sebagai Pakar Algoritma YouTube Shorts, pencerita sejarah jenius, sekaligus stand-up komedian.
    Pilihlah 1 fakta sejarah dunia yang SANGAT UNIK, ANEH, ATAU BIKIN MERINDING. Jangan yang sudah sering dibahas.
    
    ATURAN KETAT UNTUK VIRALITAS & KOMEDI:
    1. "title": Buat judul clickbait jujur yang memancing rasa penasaran (maks 60 karakter).
    2. "script_text": Maksimal 70 kata. 
       - Kalimat pertama HARUS berupa "HOOK" kuat (contoh: "Kalian pasti tertipu...", "Sejarah menyembunyikan ini...").
       - GAYA BAHASA: Harus asik, santai, kekinian (seperti ngobrol sama teman), dan SISIPKAN CANDAAN, sarkasme, atau lelucon receh di tengah cerita agar penonton tertawa. Hindari bahasa baku/kaku.
       - Kalimat terakhir HARUS memancing penonton berkomentar (contoh: "Kalian ada yang lebih absurd dari dia gak?", "Kalo lu di posisi dia, mau ngapain?").
    
    Hasilkan output HANYA dalam format JSON valid dengan struktur:
    {
      "title": "Judul clickbait viral",
      "script_text": "Naskah narasi lengkap dengan hook, candaan, dan pancingan komentar",
      "search_query_pexels": "abaikan ini"
    }
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        script_data = json.loads(raw_text)
        print(f"[+] Berhasil membuat naskah lucu! Judul: {script_data['title']}")
        return script_data
    except Exception as e:
        print("[-] Gagal memproses data JSON dari Gemini:", e)
        return None

# ==========================================
# 3. FUNGSI PEXELS (UNDUH B-ROLL VERTIKAL)
# ==========================================
def download_vertical_broll(query, filename="background_shorts.mp4"):
    print(f"[*] Mencari video di Pexels: '{query}'...")
    if not PEXELS_KEY:
        print("[-] Error: PEXELS_API_KEY tidak ditemukan!")
        return False
        
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get("videos"):
            video_url = response["videos"][0]["video_files"][0]["link"]
            print(f"[+] Mengunduh video...")
            vid_data = requests.get(video_url)
            with open(filename, 'wb') as f:
                f.write(vid_data.content)
            print(f"[+] Video disimpan: '{filename}'")
            return True
        else:
            print("[-] Video tidak ditemukan.")
            return False
    except Exception as e:
        print("[-] Gagal menghubungi Pexels API:", e)
        return False

# ==========================================
# 4. FUNGSI EDGE-TTS (VOICEOVER AMAN)
# ==========================================
def generate_voiceover(text, filename="voiceover.mp3"):
    print("[*] Menghasilkan suara AI...")
    voice = "id-ID-ArdiNeural"
    
    # Pembersihan ekstra agar command line tidak crash karena tanda kutip
    safe_text = text.replace('"', '').replace("'", "")
    
    command = f'edge-tts --voice {voice} --text "{safe_text}" --write-media {filename}'
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"[+] Suara disimpan: '{filename}'")
        return True
    except Exception as e:
        print("[-] Gagal menghasilkan suara AI:", e)
        return False

# ==========================================
# 5. FUNGSI MOVIEPY (SUBTITLE SINKRON & FONT CUSTOM)
# ==========================================
def edit_video_with_captions(video_file, audio_file, script_text, output_file="final_shorts.mp4"):
    print("[*] Merender video dengan subtitle kuning ala CapCut...")
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
        
        # Path font langsung karena file ada di root repository
        font_path = "Montserrat-Black.ttf"
        text_clips = []
        current_time = 0.0
        
        for text in chunks:
            chunk_duration = (len(text) / total_chars) * total_duration if total_chars > 0 else total_duration / len(chunks)
            chunk_duration = max(chunk_duration, 0.6) 
            
            txt_clip = TextClip(
                text, 
                fontsize=50, 
                color='yellow', # Warna subtitle kuning 
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
        
        print("[*] Proses render berjalan, mohon tunggu...")
        final_video.write_videofile(
            output_file, 
            codec="libx264", 
            audio_codec="aac", 
            fps=24,
            preset="ultrafast",
            logger=None
        )
        print(f"[+] Video Final Berhasil Dibuat: '{output_file}'")
        return True
    except Exception as e:
        print("[-] Gagal mengedit video:", e)
        return False

# ==========================================
# 6. FUNGSI YOUTUBE (OPTIMASI SEO & TAGS VIRAL)
# ==========================================
def upload_to_youtube(video_file, title, description):
    print("[*] Uploading ke YouTube dengan kategori Entertainment...")
    if not YOUTUBE_TOKEN_JSON:
        print("[-] Error: YOUTUBE_TOKEN tidak ditemukan!")
        return False
        
    try:
        token_data = json.loads(YOUTUBE_TOKEN_JSON)
        creds = Credentials.from_authorized_user_info(token_data)
        youtube = build('youtube', 'v3', credentials=creds)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['shorts', 'sejarah', 'faktaunik', 'misteri', 'funnyanimals', 'komedi', 'trending', 'lucu', 'konspirasi', 'wawasan'],
                'categoryId': '24' # Kategori Hiburan/Entertainment (Algoritma lebih suka)
            },
            'status': {
                'privacyStatus': 'public', 
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        print("[*] Mengunggah file ke channel Anda...")
        response = request.execute()
        print(f"[+] SUCCESS! Video Berhasil Diupload! Link: https://youtu.be/{response['id']}")
        return True
    except Exception as e:
        print("[-] Gagal mengupload ke YouTube:", e)
        return False

# ==========================================
# 7. BLOK EKSEKUSI UTAMA (MASTER PIPELINE)
# ==========================================
if __name__ == "__main__":
    print("=== BOT YOUTUBE SHORTS (COMEDY & ALGORITHM OPTIMIZED) ===\n")
    
    script = generate_history_short_script()
    
    if script:
        # KUNCI BACKGROUND KE VIDEO HEWAN LUCU (Sangat kontras dan lucu)
        keyword = "funny animal"
        
        # PEMBERSIH TEKS AI (Hapus bintang dan baris baru yang bikin error subtitle)
        narasi_mentah = script['script_text']
        narasi_bersih = narasi_mentah.replace('*', '').replace('\n', ' ').strip()
        judul = script['title']
        
        # DESKRIPSI DIOPTIMALKAN UNTUK SEO
        deskripsi = f"{judul}\n\nFakta sejarah dunia paling aneh! (Visual hewan lucu cuma buat pancingan hehe).\n\nMenurut kalian gimana? Coba komen di bawah!\nJangan lupa LIKE & SUBSCRIBE untuk cerita absurd lainnya!\n\n#shorts #sejarah #faktaunik #misteri #funnyanimals #komedi"
        
        broll_success = download_vertical_broll(keyword, "background_shorts.mp4")
        voice_success = generate_voiceover(narasi_bersih, "voiceover.mp3")
        
        if broll_success and voice_success:
            edit_success = edit_video_with_captions("background_shorts.mp4", "voiceover.mp3", narasi_bersih, "final_shorts.mp4")
            
            if edit_success:
                upload_to_youtube("final_shorts.mp4", judul, deskripsi)
                
        print("\n=== SELURUH PROSES SELESAI ===")
