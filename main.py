import json
import os

def generate_howto_script(topic):
    print(f"[*] Generating YouTube How-To script for topic: '{topic}'...")
    
    script = {
        "title": f"Cara Mudah {topic} untuk Pemula (Panduan Lengkap)",
        "duration": "10 Menit",
        "sections": [
            {
                "time": "0:00 - 0:45",
                "part": "Hook & Pendahuluan",
                "visual": "Cuplikan hasil akhir + wajah presenter",
                "audio": f"Pernahkah kamu kesusahan saat ingin {topic}? Di video ini, saya tunjukkan caranya dengan mudah!"
            },
            {
                "time": "0:45 - 2:30",
                "part": "Persiapan & Alat",
                "visual": "Menampilkan tools atau bahan yang dibutuhkan di layar",
                "audio": "Sebelum kita mulai, pastikan kamu sudah menyiapkan beberapa hal berikut ini..."
            },
            {
                "time": "2:30 - 8:30",
                "part": "Langkah-Langkah Utama",
                "visual": "Screen recording / demo step-by-step secara detail",
                "audio": "Mari kita masuk ke langkah pertama..."
            },
            {
                "time": "8:30 - 10:00",
                "part": "Outro & CTA",
                "visual": "Tampilan tombol Subscribe dan rekomendasi video",
                "audio": "Bagaimana, cukup mudah bukan? Jangan lupa like dan subscribe!"
            }
        ]
    }
    return script

if __name__ == "__main__":
    print("=== YouTube Long-Form How-To Bot (GitHub Actions) ===")
    
    # Ambil topik dari Environment Variable GitHub Actions, jika tidak ada baru pakai input manual
    topic_input = os.environ.get("TOPIC")
    if not topic_input:
        topic_input = input("Masukkan topik tutorial (How-To): ")
        
    result = generate_howto_script(topic_input)
    
    output_filename = "output_script.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
        
    print(f"[+] Berhasil! Skrip tersimpan di {output_filename}")
