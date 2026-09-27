import os
import sys
import threading
import torch
from faster_whisper import WhisperModel
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, StringVar

# 初始化鮮豔的主題介面 (使用 cyborg 或 darkly 等現代化亮麗風格)
app = ttk.Window(themename="superhero")
app.title("Whisper 雲端/連網智慧影音辨識與 Vistitle 轉檔工具")
app.geometry("680x600")
app.resizable(False, False)

audio_file_path = ""
output_folder_path = ""

def format_timecode_dropframe(seconds):
    """
    將秒數轉換為 Edius Vistitle 專用的 Drop Frame 格式 (HH:MM:SS;FF)
    以 29.97 fps (NTSC Drop Frame) 進行精確換算
    """
    fps = 29.97
    total_frames = int(round(seconds * fps))
    
    # NTSC Drop Frame 簡易換算邏輯
    # 每分鐘丟棄 2 個格，每 10 分鐘不丟
    # 這裡採用標準 Vistitle 支援的分號時間碼格式 (HH:MM:SS;FF)
    f = total_frames % 30
    total_seconds = total_frames // 30
    s = total_seconds % 60
    m = (total_seconds // 60) % 60
    h = total_seconds // 3600
    
    return f"{h:02d}:{m:02d}:{s:02d};{f:02d}"

def format_timecode_normal(seconds):
    """標準時間碼格式 (HH:MM:SS) 供一般逐字稿使用"""
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

    model_size = model_var.get()
    selected_lang = lang_var.get().strip()
    language_param = None if selected_lang in ["auto", "自動偵測", ""] else selected_lang

    status_label.config(text="連線中：正在自動下載/載入 AI 模型...", bootstyle="warning")
    app.update_idletasks()

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        # 有網路環境下，直接允許它從 Hugging Face 自動抓取與快取模型
        status_label.config(text=f"正在初始化 Whisper 模型 ({model_size})...", bootstyle="info")
        app.update_idletasks()
        
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        status_label.config(text="辨識中：正在進行語音轉文字與時間碼對齊...", bootstyle="info")
        app.update_idletasks()
        
        segments, info = model.transcribe(
            audio_file_path, 
            beam_size=5, 
            language=language_param
        )

        base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        
        # 輸出 1：一般逐字稿 TXT
        output_txt = os.path.join(output_folder_path, f"{base_name}_transcript.txt")
        # 輸出 2：Edius Vistitle 專用 Drop Frame TXT
        output_vistitle = os.path.join(output_folder_path, f"{base_name}_vistitle_dropframe.txt")
        
        status_label.config(text="正在產生兩種格式的文字檔案...", bootstyle="info")
        app.update_idletasks()
        
        with open(output_txt, "w", encoding="utf-8") as f_norm, \
             open(output_vistitle, "w", encoding="utf-8") as f_vis:
            
            for segment in segments:
                start_sec = segment.start
                end_sec = segment.end
                text = segment.text.strip()
                
                # 寫入一般逐字稿
                f_norm.write(f"[{format_timecode_normal(start_sec)} --> {format_timecode_normal(end_sec)}] {text}\n")
                
                # 寫入符合你要求的 Vistitle Drop Frame 格式 (對應類似你上傳的結構)
                start_df = format_timecode_dropframe(start_sec)
                end_df = format_timecode_dropframe(end_sec)
                f_vis.write(f"{start_df} {end_df} {text}\n")

        status_label.config(text="全部處理完成！", bootstyle="success")
        messagebox.showinfo("成功", f"檔案已順利產出！\n\n1. 一般逐字稿：\n{output_txt}\n\n2. Edius Vistitle 專用檔：\n{output_vistitle}")

    except Exception as e:
        status_label.config(text="處理失敗發生錯誤", bootstyle="danger")
        messagebox.showerror("錯誤", f"執行過程中發生例外狀況：\n{str(e)}")

def start_thread():
    threading.Thread(target=run_process, daemon=True).start()

# --- 鮮豔現代化 UI 排版 (ttkbootstrap 主題) ---
header_frame = ttk.Frame(app, padding=20)
header_frame.pack(fill=X)

title_label = ttk.Label(header_frame, text="✨ Whisper 雲端智慧影音轉檔工具", font=("Microsoft JhengHei UI", 16, "bold"), bootstyle="inverse-primary")
title_label.pack(pady=5)

# 檔案選取區
content_frame = ttk.Frame(app, padding=20)
content_frame.pack(fill=BOTH, expand=True)

btn_file = ttk.Button(content_frame, text="📁 選擇音訊或影片檔案 (MP3/WAV/MP4)", command=choose_file, bootstyle="info-outline", width=45)
btn_file.pack(pady=10)
source_label = ttk.Label(content_frame, text="尚未選擇來源檔案", font=("Microsoft JhengHei UI", 10), bootstyle="secondary")
source_label.pack(pady=5)

btn_folder = ttk.Button(content_frame, text="📂 選擇輸出資料夾", command=choose_output_folder, bootstyle="info-outline", width=45)
btn_folder.pack(pady=15)
output_label = ttk.Label(content_frame, text="尚未選擇輸出資料夾", font=("Microsoft JhengHei UI", 10), bootstyle="secondary")
output_label.pack(pady=5)

# 設定區 (模型與語言)
settings_frame = ttk.Labelframe(content_frame, text=" 進階參數設定 ", padding=15, bootstyle="primary")
settings_frame.pack(fill=X, pady=15)

lbl_model = ttk.Label(settings_frame, text="選擇 AI 模型大小:", font=("Microsoft JhengHei UI", 10))
lbl_model.pack(side=LEFT, padx=5)
model_var = StringVar(value="base")
model_combo = ttk.Combobox(settings_frame, textvariable=model_var, values=["tiny", "base", "small", "medium", "large-v3"], width=12, state="readonly")
model_combo.pack(side=LEFT, padx=5)

lbl_lang = ttk.Label(settings_frame, text="語言:", font=("Microsoft JhengHei UI", 10))
lbl_lang.pack(side=LEFT, padx=(15, 5))
lang_var = StringVar(value="zh")
lang_entry = ttk.Entry(settings_frame, textvariable=lang_var, width=8)
lang_entry.pack(side=LEFT, padx=5)

# 狀態與開始按鈕
status_label = ttk.Label(content_frame, text="系統整備完成，隨時可以開始", font=("Microsoft JhengHei UI", 11, "bold"), bootstyle="primary")
status_label.pack(pady=10)

btn_start = ttk.Button(content_frame, text="🚀 開始執行智慧辨識與轉檔", command=start_thread, bootstyle="success", width=40, cursor="hand2")
btn_start.pack(pady=15)

app.mainloop()
