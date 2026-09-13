"""开发服务器：文件变更时自动重建，本地预览站点。"""

import http.server
import socketserver
import threading

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from generator.builder import CONTENT, OUTPUT, TEMPLATES, Builder


class RebuildHandler(FileSystemEventHandler):
    def __init__(self):
        self._building = threading.Lock()

    def on_any_event(self, event):
        if event.src_path.endswith((".md", ".css", ".html")):
            with self._building:
                print(f"\n[变更] {event.src_path}，重建中…")
                try:
                    Builder().build()
                except Exception as exc:
                    print(f"[重建失败] {exc}")


def main():
    Builder().build()

    observer = Observer()
    observer.schedule(RebuildHandler(), str(CONTENT), recursive=True)
    observer.schedule(RebuildHandler(), str(TEMPLATES), recursive=True)
    observer.start()
    print(f"开发服务器: http://127.0.0.1:8000  (监听 {CONTENT})")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(OUTPUT), **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", 8000), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print("\n服务器已停止")


if __name__ == "__main__":
    main()
