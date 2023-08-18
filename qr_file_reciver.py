import base64
import cv2
import lt
from pyzbar.pyzbar import decode
from tqdm import tqdm


def read_file():
    camera_id = 0
    delay = 1
    window_name = 'QR File Receiver'

    cap = cv2.VideoCapture(camera_id)
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    decoder = lt.decode.LtDecoder()
    decoder.done = False
    bar = tqdm(unit="blocks", desc="Receiving file")
    bar_val = 0

    while True:
        try:
            ret, frame = cap.read()

            if ret:
                for d in decode(frame):
                    text = d.data.decode()
                    frame = cv2.rectangle(frame, (d.rect.left, d.rect.top),
                                          (d.rect.left + d.rect.width, d.rect.top + d.rect.height), (0, 255, 0), 3)
                    frame = cv2.putText(frame, text[-10:], (d.rect.left, d.rect.top + d.rect.height),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                    bytes_data = base64.b64decode(text)
                    block = lt.decode.block_from_bytes(bytes_data)
                    decoder.consume_block(block)

                    bar.total = decoder.block_graph.num_blocks
                    bar.update(len(decoder.block_graph.eliminated) - bar_val)
                    bar_val = len(decoder.block_graph.eliminated)

                    if decoder.is_done():
                        file_bytes = decoder.bytes_dump()
                        splitter = b"@@"
                        file_name_i = file_bytes.find(splitter)
                        file_name = file_bytes[:file_name_i]
                        file_data_bytes = file_bytes[file_name_i + len(splitter):]

                        with open(file_name, 'wb') as f:
                            f.write(file_data_bytes)

                cv2.imshow(window_name, frame)

            if (cv2.waitKey(delay) & 0xFF == ord('q')) or decoder.is_done():
                break
        except Exception as e:
            print(e)

    cv2.destroyWindow(window_name)


if __name__ == '__main__':
    read_file()
