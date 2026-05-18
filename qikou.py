import tkinter as tk
from tkinter import filedialog, messagebox
from pydub import AudioSegment
from pydub.silence import detect_silence
import os
import threading


# ====================== 阿岳气口删除软件 - UI 主程序 ======================
class AyueAudioTrimApp:
    def __init__(self, root):
        self.root = root
        self.root.title("阿岳气口删除软件")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        # 自动获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.ffmpeg_path = os.path.join(self.script_dir, "ffmpeg.exe")

        # 初始化 pydub（禁用 ffprobe，避免报错）
        AudioSegment.converter = self.ffmpeg_path
        AudioSegment.ffprobe = None

        # 默认参数
        self.default_input = os.path.join(self.script_dir, "mp3s")
        self.default_output = os.path.join(self.script_dir, "剪辑后音频")
        self.default_threshold = -35
        self.default_min_silence = 150
        self.default_target_silence = 80
        self.default_delete_all = False

        # 创建 UI 布局
        self.create_widgets()

    def create_widgets(self):
        # 1. 标题区域
        title_label = tk.Label(self.root, text="阿岳气口删除软件", font=("微软雅黑", 20, "bold"))
        title_label.pack(pady=15)

        # 2. 文件夹选择区域
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=10, padx=20, fill="x")

        # 输入文件夹
        tk.Label(folder_frame, text="待处理音频文件夹：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky="w",
                                                                                     pady=5)
        self.input_entry = tk.Entry(folder_frame, font=("微软雅黑", 10), width=50)
        self.input_entry.insert(0, self.default_input)
        self.input_entry.grid(row=0, column=1, padx=5)
        tk.Button(folder_frame, text="选择文件夹", command=self.select_input_folder, font=("微软雅黑", 9)).grid(row=0,
                                                                                                                column=2)

        # 输出文件夹
        tk.Label(folder_frame, text="处理后保存文件夹：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky="w",
                                                                                     pady=5)
        self.output_entry = tk.Entry(folder_frame, font=("微软雅黑", 10), width=50)
        self.output_entry.insert(0, self.default_output)
        self.output_entry.grid(row=1, column=1, padx=5)
        tk.Button(folder_frame, text="选择文件夹", command=self.select_output_folder, font=("微软雅黑", 9)).grid(row=1,
                                                                                                                 column=2)

        # 3. 参数设置区域
        param_frame = tk.LabelFrame(self.root, text="气口剪辑参数设置", font=("微软雅黑", 11, "bold"), padx=10, pady=10)
        param_frame.pack(pady=10, padx=20, fill="x")

        # 静音阈值
        tk.Label(param_frame, text="静音阈值 (dBFS)：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.threshold_entry = tk.Entry(param_frame, font=("微软雅黑", 10), width=10)
        self.threshold_entry.insert(0, str(self.default_threshold))
        self.threshold_entry.grid(row=0, column=1, padx=5)
        tk.Label(param_frame, text="（干净人声-30~-35，有底噪-35~-45）", font=("微软雅黑", 9), fg="gray").grid(row=0,
                                                                                                            column=2,
                                                                                                            sticky="w")

        # 最小气口时长
        tk.Label(param_frame, text="最小气口时长 (毫秒)：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky="w",
                                                                                       pady=5)
        self.min_silence_entry = tk.Entry(param_frame, font=("微软雅黑", 10), width=10)
        self.min_silence_entry.insert(0, str(self.default_min_silence))
        self.min_silence_entry.grid(row=1, column=1, padx=5)
        tk.Label(param_frame, text="（推荐100~200，低于此时长的停顿不处理）", font=("微软雅黑", 9), fg="gray").grid(row=1,
                                                                                                                 column=2,
                                                                                                                 sticky="w")

        # 目标气口时长
        tk.Label(param_frame, text="目标气口时长 (毫秒)：", font=("微软雅黑", 10)).grid(row=2, column=0, sticky="w",
                                                                                       pady=5)
        self.target_silence_entry = tk.Entry(param_frame, font=("微软雅黑", 10), width=10)
        self.target_silence_entry.insert(0, str(self.default_target_silence))
        self.target_silence_entry.grid(row=2, column=1, padx=5)
        tk.Label(param_frame, text="（推荐50~150，长气口剪短到此时长）", font=("微软雅黑", 9), fg="gray").grid(row=2,
                                                                                                            column=2,
                                                                                                            sticky="w")

        # 是否完全删除
        self.delete_all_var = tk.BooleanVar(value=self.default_delete_all)
        self.delete_all_check = tk.Checkbutton(param_frame, text="完全删除所有气口（不推荐，会导致声音生硬）",
                                               variable=self.delete_all_var, font=("微软雅黑", 10))
        self.delete_all_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)

        # 4. 操作按钮
        self.start_btn = tk.Button(self.root, text="开始批量处理", command=self.start_trim_thread,
                                   font=("微软雅黑", 12, "bold"), bg="#4CAF50", fg="white", width=20, height=2)
        self.start_btn.pack(pady=15)

        # 5. 日志显示区域
        log_frame = tk.LabelFrame(self.root, text="处理日志", font=("微软雅黑", 10, "bold"), padx=5, pady=5)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, font=("Consolas", 9), height=10)
        self.log_text.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="选择待处理音频文件夹")
        if folder:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="选择处理后保存文件夹")
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def start_trim_thread(self):
        # 用线程运行，避免界面卡死
        threading.Thread(target=self.start_trim, daemon=True).start()

    def start_trim(self):
        # 获取参数
        input_folder = self.input_entry.get().strip()
        output_folder = self.output_entry.get().strip()

        try:
            threshold = int(self.threshold_entry.get().strip())
            min_silence = int(self.min_silence_entry.get().strip())
            target_silence = int(self.target_silence_entry.get().strip())
            delete_all = self.delete_all_var.get()
        except ValueError:
            messagebox.showerror("参数错误", "请输入有效的数字参数！")
            return

        # 检查 ffmpeg
        if not os.path.exists(self.ffmpeg_path):
            self.log("❌ 错误：找不到 ffmpeg.exe！")
            self.log(f"请确保 ffmpeg.exe 已经放在软件同级文件夹里：{self.script_dir}")
            messagebox.showerror("缺少文件", "找不到 ffmpeg.exe！\n请将 ffmpeg.exe 放在软件同级目录下。")
            return

        # 检查输入文件夹
        if not os.path.exists(input_folder):
            self.log(f"❌ 错误：找不到输入文件夹：{input_folder}")
            messagebox.showerror("路径错误", "找不到待处理音频文件夹！")
            return

        # 创建输出文件夹
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # 查找音频文件
        support_formats = ["mp3", "wav", "m4a", "flac"]
        audio_files = []
        for root, dirs, files in os.walk(input_folder):
            for file in files:
                suffix = file.split(".")[-1].lower()
                if suffix in support_formats:
                    audio_files.append(os.path.join(root, file))

        if len(audio_files) == 0:
            self.log("❌ 错误：在输入文件夹中未找到支持的音频文件！")
            messagebox.showwarning("无文件", "未找到支持的音频文件（支持 mp3/wav/m4a/flac）")
            return

        # 开始处理
        self.start_btn.config(state="disabled", text="处理中...")
        self.log("=" * 50)
        self.log(f"✅ 成功找到 ffmpeg，准备就绪！")
        self.log(f"找到 {len(audio_files)} 个待处理音频文件，开始批量处理...")
        self.log("=" * 50)

        success_count = 0
        for audio_path in audio_files:
            file_name = os.path.basename(audio_path)
            output_path = os.path.join(output_folder, f"剪辑后_{file_name}")

            try:
                self.log(f"正在处理：{file_name}...")
                audio = AudioSegment.from_file(audio_path, format=audio_path.split(".")[-1])
                silence_segments = detect_silence(
                    audio,
                    min_silence_len=min_silence,
                    silence_thresh=threshold
                )

                output_audio = AudioSegment.empty()
                last_end = 0
                for seg_start, seg_end in silence_segments:
                    output_audio += audio[last_end:seg_start]
                    if not delete_all:
                        keep_duration = min(seg_end - seg_start, target_silence)
                        output_audio += AudioSegment.silent(duration=keep_duration)
                    last_end = seg_end
                output_audio += audio[last_end:]

                output_audio.export(output_path, format=output_path.split(".")[-1])
                self.log(f"✅ 处理完成：{file_name}")
                success_count += 1
            except Exception as e:
                self.log(f"❌ 处理失败：{file_name}，错误：{str(e)}")

        # 处理完成
        self.log("=" * 50)
        self.log(f"🎉 批量处理结束！")
        self.log(f"成功：{success_count} 个，失败：{len(audio_files) - success_count} 个")
        self.log(f"所有处理完成的文件已保存到：{output_folder}")
        self.log("=" * 50)

        self.start_btn.config(state="normal", text="开始批量处理")
        messagebox.showinfo("处理完成",
                            f"批量处理结束！\n成功：{success_count} 个\n失败：{len(audio_files) - success_count} 个")


if __name__ == "__main__":
    root = tk.Tk()
    app = AyueAudioTrimApp(root)
    root.mainloop()