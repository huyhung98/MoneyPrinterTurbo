from moviepy import VideoClip
import numpy as np

def make_frame(t):
    r = int(128 + 127 * np.sin(2 * np.pi * t / 12))
    g = int(128 + 127 * np.sin(2 * np.pi * t / 12 + 2))
    b = int(128 + 127 * np.sin(2 * np.pi * t / 12 + 4))
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
    frame[:, :] = [r, g, b]
    return frame

if __name__ == "__main__":
    clip = VideoClip(make_frame, duration=15)
    clip.write_videofile("sample_video.mp4", fps=24, codec='libx264')
    print("Created sample_video.mp4")
