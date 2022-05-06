### Requiments:
`Python 3.8.10+`

#### Install on Ubuntu:
`sudo apt install python3-opencv python3-tk python3-pil python3-pil.imagetk`

`sudo apt-get install gstreamer1.0-tools`

`sudo apt-get install libx264-dev libjpeg-dev`

`sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-ugly gstreamer1.0-tools gstreamer1.0-gl gstreamer1.0-gtk3`

#### Help Commands
`v4l2-ctl --device /dev/video0 --list-formats-ext - Вывод форматов поддерживаемых камерой`

#### RUN
`git clone https://github.com/Dimpiv/Tk_OpenCV_RPI.git`

`cd Tk_OpenCV_RPI`

`python3 main.py`
