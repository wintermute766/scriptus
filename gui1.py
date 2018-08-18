# -*- coding: utf-8 -*-
from __future__ import print_function

import queue
import subprocess
import threading
import time
from tkinter import *

from PIL import Image

filename = "./output/answer"

coords_real_1 = "40 320"
coords_real_2 = "360 460"
coords_train_1 = "40 340"
coords_train_2 = "360 480"

command_move = "xdotool mousemove {}"
command_down = "xdotool mousedown 1"
command_up = "xdotool mouseup 1"

screenshot_command = "scrot -s -q 100 {}.png &"
image_command_1 = "mogrify -modulate 100,0 -resize 300% {}.png"
image_command_2 = "./textcleaner {}.png {}.png"

ocr_command = "tesseract -l rus+eng {}.png {}"


def choose_area(coords1, coords2):
    subprocess.call([command_move.format(coords1)], shell=True)
    subprocess.call([command_down], shell=True)
    subprocess.call([command_move.format(coords2)], shell=True)
    subprocess.call([command_up], shell=True)


def screenshot_and_preprocess(filename, area):
    subprocess.call([screenshot_command.format(filename)], shell=True)
    if area == "train":
        choose_area(coords_train_1, coords_train_2)
    else:
        choose_area(coords_real_1, coords_real_2)
    time.sleep(0.5)
    subprocess.call([image_command_1.format(filename)], shell=True)
    subprocess.call([image_command_2.format(filename, filename)], shell=True)
    im = Image.open(filename + ".png")
    # print(im.format, "%dx%d" % im.size, im.mode)
    toPaste = Image.new("L", (960, 45), "white")
    box1 = (0, 105, 960, 150)
    box2 = (0, 255, 960, 300)
    im.paste(toPaste, box1)
    im.paste(toPaste, box2)
    im.save(filename + ".png")


def ocr(filename, area):
    screenshot_and_preprocess(filename, area)
    subprocess.call([ocr_command.format(filename, filename)], shell=True)


def search_query(filename, input, queue):
    with open(filename + ".txt", "r+") as f:
        contents = f.read()
        f.seek(0)
        newcontents = contents.replace('\n\n', '\n')
        f.write(newcontents)
        f.close()
    with open(filename + ".txt", "r") as f:
        contents = f.read()
        ans = contents.split("\n")
        result1 = open("./output/result1.txt", "w", encoding="utf-8")
        result2 = open("./output/result2.txt", "w", encoding="utf-8")
        result3 = open("./output/result3.txt", "w", encoding="utf-8")

        thread1 = threading.Thread(
            target=(
                lambda: perform_search(
                    input,
                    ans[0],
                    result1,
                    queue,
                    "success1")))
        thread1.start()
        # thread1.join()

        thread2 = threading.Thread(
            target=(
                lambda: perform_search(
                    input,
                    ans[1],
                    result2,
                    queue,
                    "success2")))
        thread2.start()
        # thread2.join()

        thread3 = threading.Thread(
            target=(
                lambda: perform_search(
                    input,
                    ans[2],
                    result3,
                    queue,
                    "success3")))
        thread3.start()
        thread3.join()

        result1.close()
        result2.close()
        result3.close()
        f.close()


def perform_search(input, query, result, queue, msg):
    subprocess.call(["BROWSER=w3m googler --np -n 15 " + input + " " + query], shell=True, stdout=result)
    queue.put(msg)


class GuiPart:
    def __init__(self, master, queue, ocr, search, endCommand, area):

        self.queue = queue

        self.txt1 = StringVar()
        self.txt1.set('empty')
        self.txt2 = StringVar()
        self.txt2.set('empty')
        self.txt3 = StringVar()
        self.txt3.set('empty')

        self.row = Frame(master)
        self.ent = Entry(self.row)
        self.status1 = Label(self.row, textvariable=self.txt1, fg='red')
        self.status2 = Label(self.row, textvariable=self.txt2, fg='red')
        self.status3 = Label(self.row, textvariable=self.txt3, fg='red')
        self.row.pack(side=TOP, fill=X, padx=5, pady=5)
        self.ent.pack(side=LEFT, expand=NO)
        self.status1.pack(side=LEFT)
        self.status2.pack(side=LEFT)
        self.status3.pack(side=LEFT)

        self.b1 = Button(
            master,
            text='Screenshot',
            command=(
                lambda: ocr(
                    filename,
                    area)))
        self.b1.pack(side=LEFT, padx=5, pady=5)

        self.b2 = Button(
            master, text='Search', command=(
                lambda: search(filename, self.ent.get(), queue)))
        self.b2.pack(side=LEFT, padx=5, pady=5)

        self.b3 = Button(master, text='Show')
        self.b3.pack(side=LEFT, padx=5, pady=5)

        self.b4 = Button(
            master, text='Clear files', command=(
                lambda: queue.put("wipe")))
        self.b4.pack(side=LEFT, padx=5, pady=5)

        self.b5 = Button(
            master, text='Clear text', command=(
                lambda: queue.put("clear")))
        self.b5.pack(side=LEFT, padx=5, pady=5)

        self.b6 = Button(master, text='Exit', command=endCommand)
        self.b6.pack(side=RIGHT, padx=5, pady=5)

    def processIncoming(self, master):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                if msg == 'success1':
                    self.txt1.set('success')
                    self.status1.configure(textvariable=self.txt1, fg='green')
                if msg == 'success2':
                    self.txt2.set('success')
                    self.status2.configure(textvariable=self.txt2, fg='green')
                if msg == 'success3':
                    self.txt3.set('success')
                    self.status3.configure(textvariable=self.txt3, fg='green')
                if msg == 'wipe':
                    f1 = open("./output/result1.txt", "w")
                    f2 = open("./output/result2.txt", "w")
                    f3 = open("./output/result3.txt", "w")
                    f1.write(
                        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
                    f2.write(
                        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
                    f3.write(
                        "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
                    f1.close()
                    f2.close()
                    f3.close()
                    self.txt1.set('empty')
                    self.txt2.set('empty')
                    self.txt3.set('empty')
                    self.status1.configure(textvariable=self.txt1, fg='red')
                    self.status2.configure(textvariable=self.txt2, fg='red')
                    self.status3.configure(textvariable=self.txt3, fg='red')
                if msg == 'clear':
                    self.ent.delete(0, 'end')
            except queue.Empty:
                pass


class app:
    def __init__(self, master):
        self.master = master
        self.queue = queue.Queue()
        self.gui = GuiPart(
            master,
            self.queue,
            ocr,
            search_query,
            self.endApplication,
            "train"
        )
        self.running = 1
        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming(self.master)
        if not self.running:
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    def endApplication(self):
        self.running = 0


if __name__ == '__main__':
    root = Tk()
    root.title("Клевер")
    # root.bind('<Return>', (lambda event, e=ents: fetch(e)))
    client = app(root)
    root.mainloop()
