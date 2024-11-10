import cv2
from pathlib import Path


def generateFrame(file, fps, width, height):
    path = f"Assets/Videos/{file}.mp4"
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_FPS, fps)
    target_width, target_height = width, height

    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        resizedFrame = cv2.resize(
            grayFrame, (target_width, target_height), interpolation=cv2.INTER_NEAREST
        )

        _, binary_frame = cv2.threshold(resizedFrame, 127, 1, cv2.THRESH_BINARY_INV)
        frames.append(binary_frame)

    cap.release()

    outputFile = Path(f"Assets/Videos/{file}.txt")
    outputFile.parent.mkdir(exist_ok=True, parents=True)
    with open(outputFile, "w+") as file:
        for frame in frames:
            for row in frame:
                for pixel in row:
                    file.write(str(int(pixel)))
                file.write("\n")


generateFrame("BadApple", 30, 48, 32)
