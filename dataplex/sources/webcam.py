try:
    import numpy as np
    import scipy.ndimage
    import colorsys
    import cv2
    import time
except:
    pass

from .source import Source

class SourceWebcam (Source):
    def __init__(self, camera_index: int = 2, render: bool = True):
        #--------------------------------------------------------------
        # read light values from a webcam.
        #--------------------------------------------------------------
        self.render = render
        self.width = 320
        self.height = 240

        self.capture = cv2.VideoCapture(camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def collect(self):
        """ Capture a frame. """
        rv, frame = self.capture.read()

        #------------------------------------------------------------------------
        # Sample mean and central pixels.
        # Note that OpenCV uses BGR colour space.
        #------------------------------------------------------------------------

        mean_bgr = np.sum(frame, axis=(0, 1))
        central_bgr = frame[len(frame) // 2][len(frame[0]) // 2]

        if self.render:
            # mean_bgr_image = np.array([[central_bgr]])
            # zoom = 10
            # zoomed = scipy.ndimage.zoom(mean_bgr_image, (self.height, self.width, 1), order=0)
            # display = np.concatenate((frame, zoomed), axis=1)
            # display = scipy.ndimage.zoom(display, (zoom, zoom, 1), order=0)
            cv2.imshow('frame', frame)

        #------------------------------------------------------------------------
        # Convert to RGB and extract HSB.
        #------------------------------------------------------------------------
        rgb = list(reversed(central_bgr / 255.0))
        hue, saturation, brightness = colorsys.rgb_to_hsv(*rgb)

        data = {
            "hue": hue,
            "brightness": brightness,
            "saturation": saturation
        }

        return data

    @property
    def fields(self):
        return ["hue", "saturation", "brightness"]

if __name__ == "__main__":
    source = SourceWebcam()

    while True:
        print(source.collect())
        time.sleep(0.1)
