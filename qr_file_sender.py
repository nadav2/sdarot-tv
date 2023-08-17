import base64
import os.path
from typing import List

import matplotlib.pyplot as plt
import qrcode
from matplotlib.animation import FuncAnimation
from qrcode.image.pil import PilImage


def show_qrs(images: List[PilImage], frames: List[int] = None):
    interval = 100
    if frames is not None:
        images = [images[i] for i in frames]
        for image in images:
            plt.imshow(image, cmap="gray")
            plt.show()
        return

    print(f"Num of images: {len(images)}")
    fig, ax = plt.subplots()
    im = ax.imshow(images[0], animated=True, cmap="gray")

    def update(frame):
        print(frame)
        # Update the image with the next image in the list
        im.set_array(images[frame])
        return (im,)

    anim = FuncAnimation(fig, update, frames=len(images), interval=interval, blit=True, repeat=True)
    print("Showing QR codes...", anim)
    # show plt in screen with full size
    plt.show()


def create_qr(data: str) -> PilImage:
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()
    return qr.make_image()


def send_file(path: str):
    with open(path, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode("utf-8")

    images = [create_qr(f"0@@{os.path.basename(path)}")]

    qr_size = 150
    for i in range(0, len(encoded), qr_size):
        end = i + qr_size >= len(encoded)
        step = i // qr_size + 1
        img = create_qr(f"{f'#{step}' if end else step}@@{encoded[i:i + qr_size]}")
        images.append(img)
        if end:
            for _ in range(5):
                images.append(img)

    show_qrs(images)


if __name__ == '__main__':
    send_file("server.py")
