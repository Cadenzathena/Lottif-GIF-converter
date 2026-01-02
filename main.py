import sys
import os
import subprocess
import threading
import itertools
import tkinter as tk
from tkinter import filedialog, messagebox

# Helper to find files (FFmpeg and Icon) inside the bundled EXE
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ffmpeg_path():
    return get_resource_path('ffmpeg.exe')

class ToolTip:
    """Class to create a tooltip that appears ABOVE the mouse cursor."""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay 
        self.tip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def schedule_tip(self, event=None):
        self.id = self.widget.after(self.delay, self.show_tip)

    def show_tip(self, event=None):
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() - 45 
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"), padx=5, pady=3)
        label.pack()

    def hide_tip(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

def on_custom_entry_change(*args):
    if custom_entry.get():
        output_var.set("custom")

def on_color_entry_click(event):
    if color_entry.get() == "1-256":
        color_entry.delete(0, tk.END)
        color_entry.config(fg='black')
    palette_choice.set("custom")

def on_color_entry_focus_out(event):
    if not color_entry.get():
        color_entry.insert(0, "1-256")
        color_entry.config(fg='grey')

def on_bayer_entry_click(event):
    if bayer_entry.get() == "0-5":
        bayer_entry.delete(0, tk.END)
        bayer_entry.config(fg='black')

def on_bayer_entry_focus_out(event):
    if not bayer_entry.get():
        bayer_entry.insert(0, "0-5")
        bayer_entry.config(fg='grey')

def run_ffmpeg_process():
    ffmpeg_exe = get_ffmpeg_path()
    video_path = file_entry.get().replace('"', '').strip()
    fps = fps_entry.get()
    scale_val = scale_entry.get()
    bayer_val = bayer_entry.get()

    if not video_path or not os.path.exists(video_path):
        messagebox.showerror("Error", "Please select a valid video file.")
        return

    if not (fps.isdigit() and scale_val.isdigit()):
        messagebox.showerror("Error", "FPS and Scale must be integers.")
        return

    b_val_actual = "0" if bayer_val == "0-5" else bayer_val
    if not b_val_actual.isdigit() or not (0 <= int(b_val_actual) <= 5):
        messagebox.showerror("Error", "Bayer Dither must be between 0 and 5.")
        return

    filter_list = [f"fps={fps}"]
    if denoise_var.get():
        filter_list.append("hqdn3d=1.5:1.5:3:3")
    
    scale_engine = scale_choice.get() 
    filter_list.append(f"scale={scale_val}:-1:flags={scale_engine}")
    vf_chain = ",".join(filter_list)

    b_int = int(b_val_actual)
    dither_logic = "dither=none" if b_int == 0 else f"dither=bayer:bayer_scale={b_int}"
    stats_logic = "stats_mode=diff" if diff_var.get() else "stats_mode=full"
    
    palette_filter = f"palettegen={stats_logic}"
    if palette_choice.get() == "custom":
        c_val = color_entry.get()
        if c_val.isdigit() and 1 <= int(c_val) <= 256:
            palette_filter += f":max_colors={c_val}"

    diff_logic = ":diff_mode=rectangle:new=1" if diff_var.get() else ""

    run_button.config(state="disabled")
    animate_dots()

    def worker():
        source_dir = os.path.dirname(video_path)
        filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
        save_dir = custom_entry.get().strip() if output_var.get() == "custom" else source_dir
        if not save_dir or not os.path.exists(save_dir): save_dir = source_dir 
        palette_path = os.path.join(source_dir, f"{filename_no_ext}_palette.png")
        base_output = os.path.join(save_dir, filename_no_ext)
        output_gif = f"{base_output}.gif"
        
        if os.path.exists(output_gif):
            output_gif = f"{base_output} - Copy.gif"
            counter = 2
            while os.path.exists(output_gif):
                output_gif = f"{base_output} - Copy ({counter}).gif"
                counter += 1

        try:
            cmd1 = [ffmpeg_exe, '-i', video_path, '-vf', f'{vf_chain},{palette_filter}', '-frames:v', '1', '-y', palette_path]
            cmd2 = [ffmpeg_exe, '-i', video_path, '-i', palette_path, '-lavfi', f'{vf_chain}[x];[x][1:v]paletteuse={dither_logic}{diff_logic}', '-y', output_gif]
            
            subprocess.run(cmd1, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(cmd2, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if os.path.exists(palette_path): os.remove(palette_path)
            root.after(0, lambda: finalize_ui(True, output_gif))
        except Exception as e:
            root.after(0, lambda: finalize_ui(False, str(e)))

    threading.Thread(target=worker, daemon=True).start()

def animate_dots():
    if str(run_button['state']) == "disabled":
        run_button.config(text=next(dot_cycle))
        root.after(200, animate_dots)

def finalize_ui(success, message):
    run_button.config(state="normal", text="RUN")
    if success: messagebox.showinfo("Success", f"GIF Created!\n{message}")
    else: messagebox.showerror("Error", f"An error occurred:\n{message}")

def browse_file():
    filename = filedialog.askopenfilename(title="Select Video", filetypes=(("Video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")))
    if filename:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filename)

def browse_custom_directory():
    folder = filedialog.askdirectory()
    if folder:
        custom_entry.delete(0, tk.END)
        custom_entry.insert(0, folder)
        output_var.set("custom")

# --- GUI Setup ---
root = tk.Tk()
try:
    # This points to the INTERNAL path created by PyInstaller
    icon_internal = get_resource_path("VERT_LottifIcon.ico")
    root.iconbitmap(icon_internal)
except:
    pass 

root.title("Lottif GIF Converter")
root.geometry("510x370")
root.resizable(False, False)
dot_cycle = itertools.cycle(["• • •", "  • •", "    •", "     ", "•    ", "• •  "])

# 1. Main Inputs
tk.Label(root, text="Video File:").grid(row=0, column=0, padx=(0, 10), pady=15, sticky="e")
file_entry = tk.Entry(root, width=50); file_entry.grid(row=0, column=1, sticky="w")
tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=0)

fps_lbl = tk.Label(root, text="Output FPS:"); fps_lbl.grid(row=1, column=0, padx=10, pady=5, sticky="e")
ToolTip(fps_lbl, "Higher = smoother, but much larger file size")
fps_entry = tk.Entry(root, width=10); fps_entry.insert(0, "12"); fps_entry.grid(row=1, column=1, sticky="w")

scale_lbl = tk.Label(root, text="Scale (Width):"); scale_lbl.grid(row=2, column=0, padx=10, pady=5, sticky="e")
ToolTip(scale_lbl, "Width in pixels (Height auto-calculated)")
scale_entry = tk.Entry(root, width=10); scale_entry.insert(0, "800"); scale_entry.grid(row=2, column=1, sticky="w")

pal_lbl = tk.Label(root, text="Colour Palette:"); pal_lbl.grid(row=3, column=0, padx=10, pady=5, sticky="e")
ToolTip(pal_lbl, "Auto: Best 256 colors.\nCustom: Fewer colors = smaller file size")
palette_choice = tk.StringVar(value="auto")
color_frame = tk.Frame(root); color_frame.grid(row=3, column=1, sticky="w")
tk.Radiobutton(color_frame, text="Auto", variable=palette_choice, value="auto").pack(side="left")
tk.Radiobutton(color_frame, text="Custom:", variable=palette_choice, value="custom").pack(side="left", padx=(10, 0))
color_entry = tk.Entry(color_frame, width=8, fg='grey'); color_entry.insert(0, "1-256")
color_entry.bind('<FocusIn>', on_color_entry_click); color_entry.bind('<FocusOut>', on_color_entry_focus_out)
color_entry.pack(side="left", padx=5)

dith_lbl = tk.Label(root, text="Bayer Dither:"); dith_lbl.grid(row=4, column=0, padx=10, pady=5, sticky="e")
ToolTip(dith_lbl, "0: No dither (Smallest size).\n1-5: Higher = better blending, larger size")
bayer_frame = tk.Frame(root); bayer_frame.grid(row=4, column=1, sticky="w")
bayer_entry = tk.Entry(bayer_frame, width=10, fg='grey'); bayer_entry.insert(0, "0-5")
bayer_entry.bind('<FocusIn>', on_bayer_entry_click); bayer_entry.bind('<FocusOut>', on_bayer_entry_focus_out)
bayer_entry.pack(side="left")
diff_var = tk.BooleanVar(value=True); opt_check = tk.Checkbutton(bayer_frame, text="Optimize", variable=diff_var)
opt_check.pack(side="left", padx=15); ToolTip(opt_check, "Only stores pixels that change. Lowers file size")

filter_lbl = tk.Label(root, text="Filters:"); filter_lbl.grid(row=5, column=0, padx=10, pady=5, sticky="e")
filter_frame = tk.Frame(root); filter_frame.grid(row=5, column=1, sticky="w")
scale_choice = tk.StringVar(value="lanczos")
s1 = tk.Radiobutton(filter_frame, text="Lanczos (Sharp)", variable=scale_choice, value="lanczos")
s1.pack(side="left"); ToolTip(s1, "High quality scaling. Keeps edges sharp")
s2 = tk.Radiobutton(filter_frame, text="Bicubic (Small)", variable=scale_choice, value="bicubic")
s2.pack(side="left", padx=(10,0)); ToolTip(s2, "Softer scaling. Smaller file size")
denoise_var = tk.BooleanVar(value=False); den_check = tk.Checkbutton(filter_frame, text="Denoise", variable=denoise_var)
den_check.pack(side="left", padx=15); ToolTip(den_check, "Removes grain to reduce size")

tk.Frame(root, height=2, bd=1, relief="sunken").grid(row=6, column=0, columnspan=3, sticky="ew", padx=20, pady=15)
bottom_row_frame = tk.Frame(root); bottom_row_frame.grid(row=7, column=0, columnspan=3, padx=20, sticky="ew")
output_stack = tk.Frame(bottom_row_frame); output_stack.pack(side="left", fill="y")
tk.Label(output_stack, text="Output location:", font=("Arial", 9)).pack(anchor="w", pady=(0, 8))
output_var = tk.StringVar(value="same")
tk.Radiobutton(output_stack, text="Same as source", variable=output_var, value="same").pack(anchor="w")
custom_sub_frame = tk.Frame(output_stack); custom_sub_frame.pack(anchor="w", pady=5)
tk.Radiobutton(custom_sub_frame, variable=output_var, value="custom").pack(side="left")
tk.Button(custom_sub_frame, text="Custom", command=browse_custom_directory).pack(side="left", padx=(0, 5))
custom_path_text = tk.StringVar(); custom_path_text.trace_add("write", on_custom_entry_change)
custom_entry = tk.Entry(custom_sub_frame, width=30, textvariable=custom_path_text); custom_entry.pack(side="left", padx=5)

run_button = tk.Button(bottom_row_frame, text="RUN", bg="#2ecc71", fg="white", font=("Arial", 11, "bold"), height=2, width=10, command=run_ffmpeg_process)
run_button.pack(side="right", padx=(40, 0), pady=(0, 30))

root.mainloop()