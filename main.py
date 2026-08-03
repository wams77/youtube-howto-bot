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
# 2. FUNGSI GEMINI (IDE & NASKAH ACAK/UNIK)
# ==========================================
def generate_history_short_script():
    print("[*] Meminta Gemini membuat naskah YouTube Short Sejarah yang unik...")
    if not GEMINI_KEY:
        print("[-] Error: GEMINI_API_KEY tidak ditemukan!")
        return None
        
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Menambahkan instruksi agar topik selalu di-refresh dan tidak monoton/terulang
    prompt = """
    Bertindaklah sebagai pembuat konten YouTube Shorts misteri/sejarah dunia yang kreatif.
    Pilihlah 1 fakta sejarah dunia yang SANGAT UNIK, ANEH, DAN JARANG DIKETAHUI ORANG. 
    PENTING: Jangan memilih fakta sejarah yang terlalu mainstream atau berulang. Cari dari era atau belahan dunia yang berbeda (misalnya sejarah Asia kuno, Afrika, Amerika Latin, atau Eropa pertengahan yang jarang dibahas).
    
    ATURAN KETAT:
    - Naskah narasi (script_text) MAKSIMAL 80 kata agar durasinya pas di bawah 60 detik.
    - Harus sangat memancing rasa penasaran dari detik pertama.
    
    Hasilkan output HANYA dalam format JSON valid dengan struktur:
    {
      "title": "Judul clickbait untuk metadata YouTube",
      "script_text": "Naskah narasi lengkap (Maks 80 kata)",
      "search_query_pexels": "1 kata kunci bahasa Inggris simbolis untuk video B-Roll (contoh: 'ancient ruins', 'vintage clock', 'scary forest')"
    }
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        script_data = json.loads(raw_text)
        print(f"[+] Berhasil membuat naskah unik! Judul: {script_data['title']}")
        return script_data
    except Exception as e:
        print("[-] Gagal memproses data JSON dari Gemini:", e)
        return None
# ==========================================
# 3. FUNGSI PEXELS (UNDUH B-ROLL VERTIKAL)
# ==========================================
def download_vertical_broll(query, filename="background_shorts.mp4"):
    print(f"[*] Mencari video Shorts (vertikal) di Pexels: '{query}'...")
    if not PEXELS_KEY:
        print("[-] Error: PEXELS_API_KEY tidak ditemukan!")
        return False
        
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get("videos"):
            video_url = response["videos"][0]["video_files"][0]["link"]
            print(f"[+] Mengunduh dari Pexels...")
            vid_data = requests.get(video_url)
            with open(filename, 'wb') as f:
                f.write(vid_data.content)
            print(f"[+] Video disimpan: '{filename}'")
            return True
        else:
            print("[-] Video vertikal tidak ditemukan.")
            return False
    except Exception as e:
        print("[-] Gagal menghubungi Pexels API:", e)
        return False

# ==========================================
# 4. FUNGSI EDGE-TTS (VOICEOVER AI - DIPERBAIKI)
# ==========================================
def generate_voiceover(text, filename="voiceover.mp3"):
    print("[*] Menghasilkan suara AI (Edge-TTS)...")
    voice = "id-ID-ArdiNeural" # Suara Pria Indonesia
    
    # Membersihkan teks dari tanda kutip ganda agar tidak merusak command line
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
# 5. FUNGSI MOVIEPY (EDITING VIDEO + TEKS DISESUAIKAN DENGAN AUDIO)
# ==========================================
def edit_video_with_captions(video_file, audio_file, script_text, output_file="final_shorts.mp4"):
    print("[*] Memulai proses editing video dan menyelaraskan subtitle dengan audio...")
    try:
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)
        
        # Looping video jika lebih pendek dari suara
        if video.duration < audio.duration:
            video = video.fx(loop, duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
            
        video = video.set_audio(audio)
        
        # Memecah naskah menjadi kalimat/klausa pendek agar pas dibaca
        # Kita memecah berdasarkan tanda baca atau kelompok kata yang lebih natural
        words = script_text.split(" ")
        chunks = []
        chunk_size = 3  # 3 kata per kemunculan agar dinamis
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
            
        total_duration = audio.duration
        
        # Menghitung bobot durasi berdasarkan panjang karakter tiap chunk
        # agar teks yang lebih panjang mendapat waktu tampil yang sedikit lebih lama
        total_chars = sum(len(c) for c in chunks)
        
        font_path = "Montserrat-Black.ttf"
        text_clips = []
        current_time = 0.0
        
        for text in chunks:
            # Durasi proporsional berdasarkan jumlah karakter terhadap total durasi audio
            chunk_duration = (len(text) / total_chars) * total_duration if total_chars > 0 else total_duration / len(chunks)
            # Batasi minimal durasi per chunk agar tidak terlalu kedip-kedip cepat (minimal 0.6 detik)
            chunk_duration = max(chunk_duration, 0.6)
            
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
            
        # Jika total waktu teks melebihi durasi audio, sesuaikan agar klip terakhir tidak terpotong kasar
        final_video = CompositeVideoClip([video] + text_clips)
        
        print("[*] Merender video akhir dengan sinkronisasi subtitle, mohon tunggu...")
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
        print("[-] Gagal mengedit video dengan teks berselaras:", e)
        return False
# ==========================================
# 6. FUNGSI YOUTUBE API (UPLOAD OTOMATIS)
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
                'tags': ['sejarah', 'misteri', 'faktaunik', 'shorts', 'edukasi', 'sejarahdunia'],
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
# 7. BLOK EKSEKUSI UTAMA (MASTER PIPELINE)
# ==========================================
if __name__ == "__main__":
    print("=== BOT YOUTUBE SHORTS SEJARAH (FULL AUTOMATION) ===\n")
    
    script = generate_history_short_script()
    
    if script:
        keyword = script['search_query_pexels']
        narasi = script['script_text']
        judul = script['title']
        deskripsi = f"{judul}\n\nFakta sejarah dunia yang jarang diketahui! Subscribe untuk misteri sejarah lainnya.\n#sejarah #shorts #faktaunik"
        
        broll_success = download_vertical_broll(keyword, "background_shorts.mp4")
        voice_success = generate_voiceover(narasi, "voiceover.mp3")
        
        if broll_success and voice_success:
            edit_success = edit_video_with_captions("background_shorts.mp4", "voiceover.mp3", narasi, "final_shorts.mp4")
            
            if edit_success:
                upload_to_youtube("final_shorts.mp4", judul, deskripsi)
                
        print("\n=== SELURUH PROSES SELESAI ===")
