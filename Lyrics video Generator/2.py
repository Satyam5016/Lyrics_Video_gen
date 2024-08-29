from flask import Flask, request, render_template, send_file
import os
from moviepy.editor import *
from pydub import AudioSegment
import cv2

app = Flask(__name__)

def load_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    duration = len(audio)  # Get the duration of the audio in milliseconds
    return audio, duration

def load_lyrics(file_path):
    with open(file_path, 'r') as file:
        lyrics = file.readlines()
    return lyrics

timings = [1000, 5000, 10000, 15000]  # Example timings (in milliseconds)

def generate_lyric_video(audio_file, lyrics_file, output_file, theme):
    audio, duration = load_audio(audio_file)
    lyrics = load_lyrics(lyrics_file)

    video_clips = []
    start_time = 0

    for i, line in enumerate(lyrics):
        end_time = timings[i] if i < len(timings) else duration
        duration_seconds = (end_time - start_time) / 1000

        # Create the TextClip and ensure it has a valid duration
        text_clip = TextClip(line.strip(), fontsize=70, color=text_color, size=(1280, 720), method='label')
        text_clip = text_clip.set_duration(duration_seconds).set_position('center')

        if text_clip.duration is None:
            print(f"Clip {i} has a None duration!")
        else:
            print(f"Clip {i} duration: {text_clip.duration}")

        video_clips.append(text_clip.set_start(start_time / 1000))
        start_time = end_time

    # Check all durations before concatenation
    for idx, clip in enumerate(video_clips):
        print(f"Clip {idx} duration before concatenation: {clip.duration}")

    video = concatenate_videoclips(video_clips)
    video = video.set_audio(AudioFileClip(audio_file))
    video.write_videofile(output_file, fps=24)

    audio, duration = load_audio(audio_file)
    lyrics = load_lyrics(lyrics_file)

    video_clips = []
    start_time = 0

    # Choose background based on theme
    if theme == 'dark':
        bg_color = 'black'
        text_color = 'white'
    elif theme == 'nature':
        bg_image = "nature.jpg"
    elif theme == 'space':
        bg_image = "space.jpg"
    else:
        bg_color = 'white'
        text_color = 'black'

    for i, line in enumerate(lyrics):
        end_time = timings[i] if i < len(timings) else duration

        if theme in ['nature', 'space']:
            background = ImageClip(bg_image).set_duration((end_time - start_time) / 1000)
        else:
            background = ColorClip(size=(1280, 720), color=bg_color).set_duration((end_time - start_time) / 1000)

        text_clip = TextClip(line.strip(), fontsize=70, color=text_color, size=(1280, 720), method='label')
        text_clip = text_clip.set_position('center')
        video_clips.append(CompositeVideoClip([background, text_clip]).set_start(start_time / 1000))

        start_time = end_time

    video = concatenate_videoclips(video_clips)
    video = video.set_audio(AudioFileClip(audio_file))
    video.write_videofile(output_file, fps=24)

def apply_filter(frame):
    return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

def process_video_with_opencv(video_file):
    cap = cv2.VideoCapture(video_file)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('filtered_output.mp4', fourcc, 24.0, (1280, 720), isColor=False)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        filtered_frame = apply_filter(frame)
        out.write(filtered_frame)

    cap.release()
    out.release()

@app.route('/')
def index():
    return render_template('1.html')

@app.route('/generate', methods=['POST'])
def generate():
    audio = request.files['audio']
    lyrics = request.files['lyrics']
    theme = request.form['theme']

    audio_path = os.path.join('uploads', 'merge.mp3')
    lyrics_path = os.path.join('uploads', '1.txt')
    output_path = os.path.join('uploads', 'output.mp4')

    audio.save(audio_path)
    lyrics.save(lyrics_path)

    generate_lyric_video(audio_path, lyrics_path, output_path, theme)

    # Optional: Apply OpenCV filter to the generated video
    process_video_with_opencv(output_path)

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
