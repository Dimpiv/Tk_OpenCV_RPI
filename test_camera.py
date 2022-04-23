import argparse
import datetime
import tkinter as tk
import logging
import os

import cv2
from PIL import Image, ImageTk

LOG_FORMAT = '%(levelname)-8s %(name)-12s %(message)s'
WIGHT, HEIGHT = (640, 480)

logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT
)


class Application:
    def __init__(self, output_path="./"):
        self.logger = logging.getLogger("Main_app")
        self.logger.debug("Init Camera in OpenCV")
        self.vs = cv2.VideoCapture(0)

        self.logger.debug(f"Set video size for camera: {WIGHT}X{HEIGHT}")
        self.vs.set(3, WIGHT)
        self.vs.set(4, HEIGHT)
        self.vs.set(15, 0.05)

        self.output_path = output_path  # store output path
        self.current_image = None       # current image from the camera
        self.logger.debug(f"Output path for save file: {self.output_path}")

        self.root = tk.Tk()
        self.root.title("Тест камер вместе с OpenCV")

        self.root.protocol('WM_DELETE_WINDOW', self.destructor)

        self.panel = tk.Label(self.root)
        self.panel.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        self.text = tk.Text(self.root)
        self.text.pack(fill=tk.BOTH)
        self.text.insert('1.0', 'This is a Text widget demo')

        btn = tk.Button(self.root, text="Сохранить кадр", command=self.take_snapshot)
        btn.pack(fill=tk.BOTH)

        btn = tk.Button(self.root, text="Записать видео", command=self.take_video)
        btn.pack(fill=tk.BOTH)

        self.video_loop()

    def video_loop(self):
        """ Get frame from the video stream and show it in Tkinter """
        ok, frame = self.vs.read()  # read frame from video stream
        if ok:  # frame captured without any errors
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
            self.current_image = Image.fromarray(cv2image)  # convert image for PIL
            imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
            self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector
            self.panel.config(image=imgtk)  # show the image
        self.root.after(10, self.video_loop)  # call the same function after 30 milliseconds

    def take_snapshot(self):
        """ Take snapshot and save it to the file """
        ts = datetime.datetime.now()  # grab the current timestamp
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))  # construct filename
        self.logger.debug(f"Write snapshot to: {self.output_path}{filename}")
        p = os.path.join(self.output_path, filename)  # construct output path
        snap = self.current_image.convert('RGB')
        snap.save(p, "JPEG")  # save image as jpeg file
        print("[INFO] saved {}".format(filename))

    def take_video(self):
        self.logger.debug(f"Write video sample to: {self.output_path}")

    def destructor(self):
        """ Destroy the root object and release all resources """
        print("[INFO] closing...")
        self.root.destroy()
        self.vs.release()        # release web camera
        cv2.destroyAllWindows()  # it is not mandatory in this application


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", default="./",
                help="path to output directory to store snapshots (default: current folder")
args = vars(ap.parse_args())

pba = Application(args["output"])
pba.root.mainloop()
