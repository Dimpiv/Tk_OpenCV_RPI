""" Приложение для тестирования камер с OpenCV """

import argparse
import datetime
import logging
import os
import queue
import sys
import threading
import tkinter as tk

import cv2
from PIL import Image, ImageTk

LOG_FORMAT = "%(levelname)-8s %(name)-12s %(message)s"
WIGHT, HEIGHT = (640, 480)
VIDEO_SAMPLE_LONG = 10
FPS = 15

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
        self.run = True

        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            raise ValueError("Не удается открыть поток с камеры", self.cam)

        self.frame = None

        self.log.debug(f"Установленное разрешение камеры: {WIGHT}X{HEIGHT}")
        self.cam.set(3, WIGHT)
        self.cam.set(4, HEIGHT)
        self.cam.set(5, FPS)

        threading.Thread(target=self.video_loop, daemon=False).start()

    def __del__(self):
        """Закрываем поток с камеры"""
        self.run = False
        self.cam.release()

    def video_frame(self):
        """Отдет сохраненный фрейм из видео потока"""
        return self.frame

    def video_loop(self):
        """Чтение потока с камеры"""
        while self.run:
            ok, frame = self.cam.read()
            if ok:
                self.frame = frame


class Application:
    def __init__(self, output_path="./"):
        self.logger = logging.getLogger("Main_app")
        self.vs = CamCV()

        self.output_path = output_path
        self.current_image = None

        self.signal_take_snapshot = False
        self.signal_take_video_sample = False

        self.root = tk.Tk()
        self.root.title("Тест камер с OpenCV")

        self.root.protocol("WM_DELETE_WINDOW", self.destructor)

        self.panel = tk.Label(self.root)
        self.panel.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        self.string_face_detection = tk.StringVar()
        self.label_face_detection = tk.Label(self.root, textvariable=self.string_face_detection)
        self.label_face_detection.pack(fill=tk.BOTH, padx=5, pady=1)

        self.text = tk.Text(self.root)
        self.text.pack(fill=tk.BOTH, padx=5, pady=1)

        btn = tk.Button(self.root, text="Сохранить кадр", command=self.take_snapshot)
        btn.pack(fill=tk.BOTH, padx=10, pady=5)

        btn = tk.Button(
            self.root, text=f"Записать видео {VIDEO_SAMPLE_LONG} сек. (СТОП ПРОСМОТР)", command=self.take_video
        )
        btn.pack(fill=tk.BOTH, padx=10, pady=5)

        self.frame_counter = 0  # For Face Detection
        self.face_detection_worker = FaceDetection()
        threading.Thread(target=self.face_detection_worker.worker, daemon=True).start()

        self.log_faces()
        self.main_video_loop()
        self.face_detection()

    def main_video_loop(self):
        """Получаем видеофрейм из потока"""
        if self.signal_take_snapshot:  # Запись Скриншота
            self._save_snapshot()
            self.signal_take_snapshot = False
        if self.signal_take_video_sample:  # Запись Видеосемпла
            self._save_video()
            self.signal_take_video_sample = False
        else:  # Отправляем кадры на общий поток с распознаванием и в Tkinter
            self._show_video()
        self.root.after(10, self.main_video_loop)

    def log_faces(self):
        """Проверяет статус обнаружения объекта (Лица)"""
        if self.face_detection_worker.face_detect:
            self.string_face_detection.set("Лицо в кадре!")
        else:
            self.string_face_detection.set("Никого нет")
        self.root.after(250, self.log_faces)

    def face_detection(self):
        """Отправляет в очередь на распознования лица в кадре"""
        frame = self.vs.video_frame()
        self.face_detection_worker.q.put(frame)  # Отправляем в очередь на распознование каждые 1 сек.
        self.root.after(1000, self.face_detection)

    def take_snapshot(self):
        """Сигнал для сохранения скриншота"""
        self.signal_take_snapshot = True

    def _save_snapshot(self):
        """Сохраняет скриншот в качестве имени timestamp"""
        frame = self.vs.video_frame()
        cv2_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        image = Image.fromarray(cv2_frame)
        snap = image.convert("RGB")

        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        self.logger.debug(f"Файл сохранен в: {self.output_path}{filename}")
        p = os.path.join(self.output_path, filename)

        snap.save(p, "JPEG")

        self.text.insert(tk.END, f"Сохранен файл: {filename}" + "\n")
        self.logger.debug(f"Сохранен файл изображение: {self.output_path}{filename}")

    def take_video(self):
        """Сигнал для запуска записи видео"""
        self.signal_take_video_sample = True

    def _save_video(self):
        """Сохраняет видео в качестве имени timestamp  !!! BAD БЛОКИРУЮЩИЙ МЕТОД"""
        ts = datetime.datetime.now()
        filename = "{}.avi".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        video_out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc("M", "J", "P", "G"), FPS, (WIGHT, HEIGHT))
        self.logger.debug("Старт записи видео!")
        self.text.insert(tk.END, f"Идет запись видео семпла - {VIDEO_SAMPLE_LONG} секунд" + "\n")

        while True:
            frame = self.vs.video_frame()
            video_out.write(frame)
            if ts + datetime.timedelta(seconds=VIDEO_SAMPLE_LONG) < datetime.datetime.now():
                self.logger.debug("Запись завершена!")
                self.text.insert(tk.END, "Запись завершена!\n")
                break
        self.text.insert(tk.END, f"Сохранен файл: {filename}" + "\n")
        self.logger.info(f"Сохранен файл видео: {self.output_path}{filename}")

    def _show_video(self):
        """Передает полученный фрейм видеопотка в Tkinter"""
        frame = self.vs.video_frame()
        # cv2_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        cv2_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Вроде работает пошустрее ???
        self.current_image = Image.fromarray(cv2_frame)
        img_tk = ImageTk.PhotoImage(image=self.current_image)
        self.panel.img_tk = img_tk
        self.panel.config(image=img_tk)

    def destructor(self):
        """Завершаем все процессы"""
        self.logger.info("Закрытие программы")
        self.vs.run = False
        self.root.destroy()
        cv2.destroyAllWindows()
        sys.exit(0)


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
