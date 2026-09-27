import os
import sys
import threading
import torch
import torchaudio
from faster_whisper import WhisperModel
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, StringVar

app = ttk.Window(themename="superhero")
app.title("Whisper 智慧影音轉檔與進度追蹤工具")
app.geometry("680x620")
app.resizable(False, False)

audio_file_path = ""
output_folder_path = ""

# 語言下拉選單：清楚顯示中文名稱與代碼
LANGUAGES = {
    "中文 (zh)": "zh",
    "英文 (en)": "en",
    "日文 (ja)": "ja",
    "西班牙文 (es)": "es",
    "法文 (fr)": "fr",
    "德文 (de)": "de",
    "義大利文 (it)": "it",
    "印地文 / 尼泊爾語 (hi)": "hi",
    "印尼文 (id)": "id",
    "AUTO 自動判讀 (auto)": "auto"
}

def format_timecode(seconds):
    """標準時間碼格式 (HH:MM:SS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def choose_file():
    global audio_file_path
    file_path = filedialog.askopenfilename(
        title="選擇語音或影片檔案",
        filetypes=[("支援的音訊/視訊", "*.mp3;*.wav;*.m4a;*.mp4;*.mkv;*.flac"), ("所有檔案", "*.*")]
    )
    if not file_path:
        return
    audio_file_path = file_path
    source_label.config(text=f"已選檔案：{os.path.basename(file_path)}", bootstyle="success")

def choose_output_folder():
    global output_folder_path
    folder_path = filedialog.askdirectory(title="選擇輸出資料夾")
    if not folder_path:
        return
    output_folder_path = folder_path
    output_label.config(text=f"已選資料夾：{output_folder_path}", bootstyle="success")

def run_process():
    global audio_file_path, output_folder_path
    
    if not audio_file_path or not output_folder_path:
        messagebox.showwarning("提醒", "請先完整選擇『音訊檔案』與『輸出資料夾』！")
        return

    selected_display_lang = lang_var.get()
    language_code = LANGUAGES.get(selected_display_lang, "auto")
    language_param = None if language_code == "auto" else language_code

    model_size = model_var.get()

    status_label.config(text="正在分析音訊檔案長度...", bootstyle="warning")
    app.update_idletasks()

    try:
        info_audio = torchaudio.info(audio_file_path)
        total_duration = info_audio.num_frames / info_audio.sample_rate
    except Exception:
        total_duration = 0

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        status_label.config(text=f"正在載入 AI 模型 ({model_size})...", bootstyle="info")
        progress_bar['value'] = 10
        app.update_idletasks()
        
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        status_label.config(text="辨識中：AI 正在轉寫語音內容...", bootstyle="info")
        progress_bar['value'] = 20
        app.update_idletasks()
        
        segments, info = model.transcribe(
            audio_file_path, 
            beam_size=5, 
            language=language_param
        )

        base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        output_txt = os.path.join(output_folder_path, f"{base_name}_transcript.txt")
        output_timecode = os.path.join(output_folder_path, f"{base_name}_timecode.txt")
        
        all_segments = []
        for seg in segments:
            all_segments.append(seg)

        status_label.config(text="正在產出兩種格式的文字檔案...", bootstyle="info")
        progress_bar['value'] = 90
        app.update_idletasks()

        with open(output_txt, "w", encoding="utf-8") as f_pure, \
             open(output_timecode, "w", encoding="utf-8") as f_tc:
            
            for segment in all_segments:
                start_str = format_timecode(segment.start)
                end_str = format_timecode(segment.end)
                text = segment.text.strip()
                
                # 1. 純文字逐字稿
                f_pure.write(f"{text}\n")
                # 2. 帶標準時間碼 TXT
                f_tc.write(f"[{start_str} --> {end_str}] {text}\n")

                if total_duration > 0:
                    pct = min(95, 20 + int((segment.end / total_duration) * 75))
                    progress_bar['value'] = pct
                    percent_label.config(text=f"處理進度：{pct}%")
                    app.update_idletasks()

        progress_bar['value'] = 100
        percent_label.config(text="處理進度：100%")
        status_label.config(text="全部處理完成！", bootstyle="success")
        
        messagebox.showinfo("成功", f"檔案已順利產出！\n\n1. 純文字逐字稿：\n{output_txt}\n\n2. 標準帶時間碼檔：\n{output_timecode}")

    except Exception as e:
        status_label.config(text="處理失敗發生錯誤", bootstyle="danger")
        messagebox.showerror("錯誤", f"執行過程中發生例外狀況：\n{str(e)}")

def start_thread():
    progress_bar['value'] = 0
    percent_label.config(text="處理進度：0%")
    threading.Thread(target=run_process, daemon=True).start()

# --- 介面排版 ---
header_frame = ttk.Frame(app, padding=15)
header_frame.pack(fill=X)

title_label = ttk.Label(header_frame, text="✨ Whisper 影音智慧轉檔工具", font=("Microsoft JhengHei UI", 16, "bold"), bootstyle="inverse-primary")
title_label.pack(pady=5)

content_frame = ttk.Frame(app, padding=15)
content_frame.pack(fill=BOTH, expand=True)

btn_file = ttk.Button(content_frame, text="📁 選擇音訊或影片檔案 (MP3/WAV/MP4)", command=choose_file, bootstyle="info-outline", width=45)
btn_file.pack(pady=8)
source_label = ttk.Label(content_frame, text="尚未選擇來源檔案", font=("Microsoft JhengHei UI", 9), bootstyle="secondary")
source_label.pack(pady=2)

btn_folder = ttk.Button(content_frame, text="📂 選擇輸出資料夾", command=choose_output_folder, bootstyle="info-outline", width=45)
btn_folder.pack(pady=10)
output_label = ttk.Label(content_frame, text="尚未選擇輸出資料夾", font=("Microsoft JhengHei UI", 9), bootstyle="secondary")
output_label.pack(pady=2)

# 進階設定區
settings_frame = ttk.Labelframe(content_frame, text=" 進階參數設定 ", padding=12, bootstyle="primary")
settings_frame.pack(fill=X, pady=10)

model_frame = ttk.Frame(settings_frame)
model_frame.pack(fill=X, pady=5)
lbl_model = ttk.Label(model_frame, text="AI 模型大小:", font=("Microsoft JhengHei UI", 9), width=12)
lbl_model.pack(side=LEFT, padx=5)
model_var = StringVar(value="base")
model_combo = ttk.Combobox(model_frame, textvariable=model_var, values=["tiny", "base", "small", "medium", "large-v3"], width=22, state="readonly")
model_combo.pack(side=LEFT, padx=5)

lang_frame = ttk.Frame(settings_frame)
lang_frame.pack(fill=X, pady=5)
lbl_lang = ttk.Label(lang_frame, text="辨識語言:", font=("Microsoft JhengHei UI", 9), width=12)
lbl_lang.pack(side=LEFT, padx=5)
lang_var = StringVar(value="中文 (zh)")
lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, values=list(LANGUAGES.keys()), width=22, state="readonly")
lang_combo.pack(side=LEFT, padx=5)

# 進度條與狀態顯示區
progress_frame = ttk.Frame(content_frame, padding=5)
progress_frame.pack(fill=X, pady=10)

status_label = ttk.Label(progress_frame, text="系統整備完成，隨時可以開始", font=("Microsoft JhengHei UI", 10, "bold"), bootstyle="primary")
status_label.pack(anchor="w", pady=2)

progress_bar = ttk.Progressbar(progress_frame, orient=HORIZONTAL, length=600, mode='determinate', bootstyle="success-striped")
progress_bar.pack(fill=X, pady=5)

percent_label = ttk.Label(progress_frame, text="處理進度：0%", font=("Microsoft JhengHei UI", 9), bootstyle="info")
percent_label.pack(anchor="e", pady=2)

btn_start = ttk.Button(content_frame, text="🚀 開始執行智慧辨識與轉檔", command=start_thread, bootstyle="success", width=40, cursor="hand2")
btn_start.pack(pady=8)

app.mainloop()
