import os
import tempfile
import shutil
from flask import Flask, render_template, request, jsonify
from pydub import AudioSegment

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    album_info = request.form['album_info']

    # Check if the file is an MP3
    if file.filename.endswith('.mp3'):
        try:
            # Create a temporary folder to store the split audio files
            temp_folder = tempfile.mkdtemp()

            # Save the uploaded file to the temporary folder
            file_path = os.path.join(temp_folder, file.filename)
            file.save(file_path)

            # Split the MP3 file based on the timestamps
            song_list = parse_album_info(album_info)
            split_songs(temp_folder, file_path, song_list)

            # Create the output folder path
            output_folder = os.path.join(app.root_path, 'uploads', 'split_files')

            # Create the output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            # Move the split audio files to the output folder
            move_split_files(temp_folder, output_folder)

            return jsonify({'success': 'Album split successfully', 'folder': output_folder})
        except Exception as e:
            return jsonify({'error': 'Error splitting album', 'details': str(e)})
        finally:
            # Remove the temporary folder and its contents
            shutil.rmtree(temp_folder)

    return jsonify({'error': 'Invalid file format'})

def parse_album_info(album_info):
    # Parse the album info and extract timestamps and song names
    song_list = []
    lines = album_info.split('\n')
    for line in lines:
        if line.strip():
            timestamp, song_name = line.strip().split(' ', 1)
            song_list.append({'timestamp': timestamp, 'name': song_name})
    return song_list

def split_songs(output_folder, file_path, song_list):
    # Load the MP3 file
    audio = AudioSegment.from_mp3(file_path)

    # Split the songs and save them
    for i, song in enumerate(song_list):
        start_time = parse_timestamp(song['timestamp'])
        if i < len(song_list) - 1:
            end_time = parse_timestamp(song_list[i + 1]['timestamp'])
        else:
            end_time = len(audio)  # Last song ends at the end of the file

        # Extract the song segment
        song_segment = audio[start_time:end_time]

        # Create the output file path
        output_file = os.path.join(output_folder, f"{song['name']}.mp3")

        # Save the song segment
        song_segment.export(output_file, format="mp3")
        print(f"Split {song['name']} at {song['timestamp']} to {output_file}")

def parse_timestamp(timestamp):
    # Parse the timestamp and convert it to milliseconds
    minutes, seconds = timestamp.split(':')
    total_seconds = int(minutes) * 60 + int(seconds)
    return total_seconds * 1000

def move_split_files(source_folder, destination_folder):
    for file_name in os.listdir(source_folder):
        source_path = os.path.join(source_folder, file_name)
        destination_path = os.path.join(destination_folder, file_name)
        try:
            shutil.move(source_path, destination_path)
        except Exception as e:
            raise Exception(f"Error moving file '{file_name}' to destination folder: {str(e)}")

if __name__ == '__main__':
    app.run(debug=False)
