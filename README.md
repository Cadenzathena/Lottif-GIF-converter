# Lottif GIF Converter

A local native windows desktop application that gives quick options for converting video files to the GIF format. Written on a single python script and uses Tkinter for the GUI. Utilizes the ffmpeg binary to handle conversion and optimization.

<p align="center"><img width="350" alt="Screenshot 2026-01-02 165647" src="https://github.com/user-attachments/assets/b13848c7-b486-4f28-94ee-06778ee367dd" /></p>

ffmpeg is an incredibly powerful and efficient tool, however I found it a bit tedious to test GIF optimization with all their various settings in the command line. I also like GUIs and didn't want to use a web based GIF converter.

<br>

## 📋 Features
- Change output FPS
- Change output scale width (Height will be auto calculated to preserve aspect ratio)
- Choose amount of colours per frame or auto palettegen
- Bayer dither range to mask banding
- Lanczos or Bicubic filtering options
- GIF optimization checkbox for storing only the pixels that change
- Denoise checkbox to remove banding

<p align="center"><img alt="nemupanart gif" src="https://github.com/user-attachments/assets/b569bc43-b9cf-4aa7-907a-4b7e72469e35" /></p>

<p align="center">
Original video from <a href="https://x.com/nemupanart/status/1991918283256398189?s=20">@nemupanart</a>
</p>

<br>

## ℹ️ Requirements
- ffmpeg is not required to added to your system PATH as the release version has the binary bundled inside the executable. If you do have ffmpeg added to your system path then Lottif will detect it and use that version instead.
- You can clone this repository and use the main.py script instead of the release executable. You'll need python installed and ffmpeg added to your system PATH
- Building this application requires pyinstaller

<br>

## 🛠️ Building
1. clone this repo
 `git clone https://github.com/Cadenzathena/Lottif-GIF-converter.git`

2. open the directory location in the terminal of your choice

3. Run `pyinstaller --noconsole --onefile --add-binary "ffmpeg.exe;." --add-data "VERT_LottifIcon.ico;." --icon="icon.ico" --name "Lottif GIF Converter" main.py`

<br>

> [!note]
> ensure that the ico file in the directory and build command is also updated in main.py
> <br>
> <a href="https://ffmpeg.org/download.html">Get the official ffmpeg binary</a> to bundle it in the final executable.
