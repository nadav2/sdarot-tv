import base64
import io
import os.path
import cv2
import lt
import numpy as np
import qrcode
from qrcode.image.pil import PilImage


def create_qr(data: str) -> PilImage:
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()
    return qr.make_image()


def send_file(path: str):
    cv_window_name = "QR File Sender"
    cv2.namedWindow(cv_window_name, cv2.WINDOW_NORMAL)

    block_size = 100
    with open(path, 'rb') as f:
        file_data = f.read()

    file_name = os.path.basename(path)
    file_name_wrapper = file_name.encode("utf-8") + b"@@"
    f = io.BytesIO(file_name_wrapper + file_data)

    encoder = lt.encode.encoder(f, block_size)
    for i, block in enumerate(encoder):
        encoded = base64.b64encode(block).decode("utf-8")
        qr = create_qr(encoded)

        pil_image = qr.convert('RGB')
        open_cv_image = np.array(pil_image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()

        cv2.imshow(cv_window_name, open_cv_image)

        print(f"Showing QR code {i}")
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break


if __name__ == '__main__':
    send_file("gpx/tupuzina_granot.gpx")
