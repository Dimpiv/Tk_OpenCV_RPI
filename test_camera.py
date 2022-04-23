""" Приложение для тестирования камер с OpenCV """

import argparse
import datetime
import logging
import os
import queue
import threading
import time
import tkinter as tk

import cv2
from PIL import Image, ImageTk

LOG_FORMAT = "%(levelname)-8s %(name)-12s %(message)s"
WIGHT, HEIGHT = (640, 480)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


class FaceDetection:
    """Класс распознавателя лица для работы в отдельном потоке"""

    def __init__(self):
        self.q = queue.Queue()
        self.face_cascade = cv2.CascadeClassifier("./haarcascade_frontalface_default.xml")
        self.face_detect = False

    def worker(self):
        while True:
            frame = self.q.get()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            if not isinstance(faces, tuple):
                self.face_detect = True
            else:
                self.face_detect = False

            self.q.task_done()


class CamCV:
    """Получение и Обрабока видеопотока с камеры"""

    def __init__(self):
        self.log = logging.getLogger("Cam_app")
        self.prev_frame_time = 0
        self.fps_value = None

        self.log.debug("Init Camera in OpenCV")
        self.cam = cv2.VideoCapture(0)

        self.log.debug(f"Set video size for camera: {WIGHT}X{HEIGHT}")
        self.cam.set(3, WIGHT)
        self.cam.set(4, HEIGHT)
        self.cam.set(5, 30)

        self.counter = 0

        self.face_detection_worker = FaceDetection()
        threading.Thread(target=self.face_detection_worker.worker, daemon=True).start()

    def __del__(self):
        """Закрываем поток с камеры"""
        self.cam.release()

    def video_frame(self):
        """Отдет фрейм из видео потока"""
        ok, frame = self.cam.read()
        if ok:
            self.counter += 1
            new_frame_time = time.time()
            self.fps_value = 1 / (new_frame_time - self.prev_frame_time)
            self.prev_frame_time = new_frame_time

            if self.counter >= 30:
                self.face_detection_worker.q.put(frame)
                self.counter = 0

            return ok, cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
        return None, None

    def get_fps(self):
        return int(self.fps_value)

    def get_face_detect(self):
        return self.face_detection_worker.face_detect


class Application:
    def __init__(self, output_path="./"):
        self.logger = logging.getLogger("Main_app")
        self.vs = CamCV()

        self.output_path = output_path  # store output path
        self.current_image = None  # current image from the camera
        self.logger.debug(f"Output path for save file: {self.output_path}")

        self.root = tk.Tk()
        self.root.title("Тест камер с OpenCV")

        self.root.protocol("WM_DELETE_WINDOW", self.destructor)

        self.panel = tk.Label(self.root)
        self.panel.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        self.string_fps = tk.StringVar()
        self.label_fps = tk.Label(self.root, textvariable=self.string_fps)
        self.label_fps.pack(fill=tk.BOTH, padx=5, pady=1)

        self.text = tk.Text(self.root)
        self.text.pack(fill=tk.BOTH, padx=5, pady=1)

        btn = tk.Button(self.root, text="Сохранить кадр", command=self.take_snapshot)
        btn.pack(fill=tk.BOTH, padx=10, pady=5)

        btn = tk.Button(self.root, text="Записать видео", command=self.take_video)
        btn.pack(fill=tk.BOTH, padx=10, pady=5)

        self.string_fps.set("FPS: 0")

        self.video_loop()
        self.log_faces()

    def video_loop(self):
        """Получаем видеофрейм из потока, конвертируем для отображения и открываем его в Tkinter"""
        ok, cv2image = self.vs.video_frame()
        if ok:
            self.current_image = Image.fromarray(cv2image)  # convert image for PIL
            imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
            self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector
            self.panel.config(image=imgtk)  # show the image
        self.root.after(5, self.video_loop)  # call the same function after 5 milliseconds
        self.string_fps.set(f"FPS: {self.vs.get_fps()}")

    def log_faces(self):
        """Проверяет статус обнаружения объекта (Лица)"""
        if self.vs.get_face_detect():
            ts = datetime.datetime.now()
            self.text.insert(tk.END, "{} - Лицо в кадре!\n".format(ts.strftime("%H-%M-%S")))
        self.root.after(1000, self.log_faces)

    def take_snapshot(self):
        """Сохраняем кадр в качестве имени timestamp"""
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        self.logger.debug(f"Write snapshot to: {self.output_path}{filename}")
        p = os.path.join(self.output_path, filename)
        snap = self.current_image.convert("RGB")
        snap.save(p, "JPEG")
        self.text.insert(tk.END, f"Сохранен файл: {filename}" + "\n")
        self.logger.info(f"Сохранен файл изображение: {self.output_path}{filename}")

    def take_video(self):
        """FUTURE Functional"""
        ts = datetime.datetime.now()
        filename = "{}.mp4".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        self.text.insert(tk.END, f"Сохранен файл: {filename}" + "\n")
        self.logger.info(f"Сохранен файл видео: {self.output_path}")

    def destructor(self):
        """Завершаем все процессы"""
        self.logger.info("Закрытие программы")
        self.root.destroy()
        cv2.destroyAllWindows()


ap = argparse.ArgumentParser()
ap.add_argument(
    "-o",
    "--output",
    default="./",
    help="path to output directory to store snapshots (default: current folder",
)
args = vars(ap.parse_args())

pba = Application(args["output"])
pba.root.mainloop()
