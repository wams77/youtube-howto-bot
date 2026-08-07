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
# 2. FUNGSI GEMINI (IDE SEJARAH ANTI-DUPLIKAT)
# ==========================================
def generate_history_short_script():
    print("[*] Meminta Gemini membuat naskah sejarah yang unik...")
    if not GEMINI_KEY:
        print("[-] Error: GEMINI_API_KEY tidak ditemukan!")
        return None
        
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Bertindaklah sebagai pembuat konten YouTube Shorts misteri/sejarah dunia.
    Pilihlah 1 fakta sejarah dunia yang SANGAT UNIK, ANEH, DAN JARANG DIKETAHUI ORANG. 
    PENTING: Jangan memilih fakta sejarah yang mainstream atau sudah sering dibahas. Cari dari era atau belahan dunia yang berbeda setiap kalinya agar tidak berulang.
    
    ATURAN KETAT:
    - Naskah narasi (script_text) MAKSIMAL 80 kata.
    - Harus langsung memancing rasa penasaran dari detik pertama.
    
    Hasilkan output HANYA dalam format JSON valid dengan struktur:
    {
      "title": "Judul clickbait untuk metadata YouTube",
      "script_text": "Naskah narasi lengkap (Maks 80 kata)",
      "search_query_pexels": "abaikan ini"
    }
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
# 3. FUNGSI PEXELS (UNDUH B-ROLL)
# ==========================================
def download_vertical_broll(query, filename="background_shorts.mp4"):
    print(f"[*] Mencari video Shorts di Pexels dengan kata kunci: '{query}'...")
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
    print("[*] Menghasilkan suara AI (Edge-TTS)...")
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
    print("[*] Memulai proses editing video dan subtitle...")
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
        chunk_size = 3  # 3 kata per layar
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
            
        total_duration = audio.duration
        total_chars = sum(len(c) for c in chunks)
        
        font_path = "Montserrat-Black.ttf"
        text_clips = []
        current_time = 0.0
        
        for text in chunks:
            # Mengatur kecepatan teks berdasarkan panjang karakter agar natural
            chunk_duration = (len(text) / total_chars) * total_duration if total_chars > 0 else total_duration / len(chunks)
            chunk_duration = max(chunk_duration, 0.6) # Minimal 0.6 detik agar tidak berkedip cepat
            
            txt_clip = TextClip(
                text, 
                fontsize=45, 
                color='white', 
                font=font_path, 
                stroke_color='black', 
                stroke_width=2,
                size=(video.w - 80, None), 
                method='caption'
            )
            
            txt_clip = txt_clip.set_start(current_time)
            txt_clip = txt_clip.set_duration(chunk_duration)
            txt_clip = txt_clip.set_position(('center', 'center'))
            text_clips.append(txt_clip)
            
            current_time += chunk_duration
            
        final_video = CompositeVideoClip([video] + text_clips)
        
        print("[*] Merender video akhir, mohon tunggu...")
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
        print("[-] Gagal mengedit video dengan teks:", e)
        return False

# ==========================================
# 6. FUNGSI YOUTUBE (UPLOAD OTOMATIS)
# ==========================================
def upload_to_youtube(video_file, title, description):
    print("[*] Memulai proses upload ke YouTube...")
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
                'tags': ['sejarah', 'misteri', 'faktaunik', 'shorts', 'funnyanimals', 'edukasi'],
                'categoryId': '27' 
            },
            'status': {
                'privacyStatus': 'public', 
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        print("[*] Mengunggah file ke channel Anda...")
        response = request.execute()
        print(f"[+] SUCCESS! Video Berhasil Diupload! Link: https://youtu.be/{response['id']}")
        return True
    except Exception as e:
        print("[-] Gagal mengupload ke YouTube:", e)
        return False

# ==========================================
# 7. BLOK EKSEKUSI UTAMA
# ==========================================
if __name__ == "__main__":
    print("=== BOT YOUTUBE SHORTS (FULL AUTOMATION) ===\n")
    
    script = generate_history_short_script()
    
    if script:
        # KUNCI BACKGROUND KE VIDEO HEWAN LUCU
        keyword = "funny animal"
        
        # PEMBERSIH TEKS: Menghapus bintang/enter yang sering dibuat oleh AI
        narasi_mentah = script['script_text']
        narasi_bersih = narasi_mentah.replace('*', '').replace('\n', ' ').strip()
        
        judul = script['title']
        deskripsi = f"{judul}\n\nFakta sejarah dunia yang jarang diketahui! Visual hanya pemanis ya hehe.\nSubscribe untuk konten menarik lainnya!\n#shorts #sejarah #faktaunik #funnyanimals"
        
        broll_success = download_vertical_broll(keyword, "background_shorts.mp4")
        voice_success = generate_voiceover(narasi_bersih, "voiceover.mp3")
        
        if broll_success and voice_success:
            edit_success = edit_video_with_captions("background_shorts.mp4", "voiceover.mp3", narasi_bersih, "final_shorts.mp4")
            
            if edit_success:
                upload_to_youtube("final_shorts.mp4", judul, deskripsi)
                
        print("\n=== SELURUH PROSES SELESAI ===")
