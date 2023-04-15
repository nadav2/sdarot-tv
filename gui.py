import multiprocessing
import time
import webview
import server

port = 12055


def main():
    shared_value = multiprocessing.Value("b", False)

    server_process = multiprocessing.Process(target=server.main, args=(port, shared_value), daemon=True)
    server_process.start()

    while not shared_value.value:
        time.sleep(0.1)

    webview.create_window('Sdarot.TV Downloader', f"http://localhost:{port}")
    webview.start()


if __name__ == '__main__':
    main()
