import subprocess
from core.logger import Logginglogger
from queue import Queue, Empty
from threading import Thread
import os


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


def run():
    botdir = './core/bots/'
    lst = os.listdir(botdir)
    runlst = []
    for x in lst:
        bot = f'{botdir}{x}/bot.py'
        if os.path.exists(bot):
            p = subprocess.Popen(f'python {bot}', shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            runlst.append(p)
    q = Queue()
    threads = []
    for p in runlst:
        threads.append(Thread(target=enqueue_output, args=(p.stdout, q)))

    for t in threads:
        t.daemon = True
        t.start()

    while True:
        try:
            line = q.get_nowait()
        except Empty:
            pass
        else:
            Logginglogger(format="[Akaribot]").info(line.decode('utf8'))

        # break when all processes are done.
        if all(p.poll() is not None for p in runlst):
            break