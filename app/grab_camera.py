import numpy as np
import subprocess

def decode_to_jpg(yuv_csv):
    temp_yuv_file = "tmp/temp.yuv"
    yuv_array = np.array(yuv_csv.split(',')[8:],np.uint8)
    # yuv_array_temp = np.fromstring(yuv_csv, sep=",", dtype=np.uint8)
    # yuv_array = yuv_array_temp[8:]

    # # Save raw YUV data to a temporary file
    # with open(temp_yuv_file, "wb") as f:
    #     f.write(yuv_array.tobytes())



    # Use FFmpeg to convert YUV to JPG
    ffmpeg_command = [
        "ffmpeg",
        "-f", "rawvideo",
        "-s", "320x240",  # Set resolution
        "-pix_fmt", "yuyv422",  # Set pixel format
        # "-i", "tmp/temp.yuv",  # Input file
        "-i", "pipe:0",  # Input file
        "-frames:v", "1",  # Extract 1 frame
        "-f", "mjpeg",
        "-y",
        "pipe:1"  # Output file
    ]

    # print(subprocess.check_output(ffmpeg_command, input=yuv_array.tobytes()), flush=True)
    process = subprocess.run(ffmpeg_command, check=True, input=yuv_array.tobytes(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode != 0:
        return f"Error converting image", 500
    # print(f"Saved {output_filename}")
    return process.stdout
