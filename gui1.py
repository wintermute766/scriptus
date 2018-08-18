# -*- coding: utf-8 -*-
import queue
import subprocess
import threading
import time
from tkinter import *

from PIL import Image

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


class GuiPart:
    def __init__(self, root, queue, ocr, ocr_only, search, visualize, wipe, end_command, area):

        self.queue = queue
        self.search = search
        self.wipe = wipe

        self.txt1 = StringVar()
        self.txt1.set('empty')
        self.txt2 = StringVar()
        self.txt2.set('empty')
        self.txt3 = StringVar()
        self.txt3.set('empty')

        # row 1

        self.row1 = Frame(root)

        self.query = Entry(self.row1)
        self.query.focus_set()

        self.status1 = Label(self.row1, textvariable=self.txt1, fg='red', padx=5, pady=5)
        self.status2 = Label(self.row1, textvariable=self.txt2, fg='red', padx=5, pady=5)
        self.status3 = Label(self.row1, textvariable=self.txt3, fg='red', padx=5, pady=5)

        self.filename = Entry(self.row1)
        self.filename.insert(END, 'output/answer')

        self.row1.pack(fill=X, padx=5, pady=5)
        self.query.pack(side=LEFT, expand=NO)
        self.status1.pack(side=LEFT)
        self.status2.pack(side=LEFT)
        self.status3.pack(side=LEFT)
        self.filename.pack(side=RIGHT)

        # row 2

        self.row2 = Frame(root)

        self.row2.pack(fill=X, padx=5, pady=5)

        self.b1 = Button(self.row2, text='Screenshot', command=(lambda: ocr(self.filename.get(), area)))
        self.b1.pack(side=LEFT, padx=5, pady=5)

        self.b2 = Button(self.row2, text='Search',
                         command=(lambda: search(self.filename.get(), self.query.get(), queue)))
        self.b2.pack(side=LEFT, padx=5, pady=5)

        self.b3 = Button(self.row2, text='Show', command=(lambda: visualize(self.filename.get(), self.query.get())))
        self.b3.pack(side=LEFT, padx=5, pady=5)

        # row 3

        self.row3 = Frame(root)
        self.row3.pack(fill=X, padx=5, pady=5)

        self.b4 = Button(self.row3, text='Clear files', command=(lambda: queue.put("wipe")))
        self.b4.pack(side=LEFT, padx=5, pady=5)

        self.b7 = Button(self.row3, text='Exit', command=end_command)
        self.b7.pack(side=RIGHT, padx=5, pady=5)

        self.b5 = Button(self.row3, text='Clear text', command=(lambda: queue.put("clear")))
        self.b5.pack(side=RIGHT, padx=5, pady=5)

        self.b6 = Button(self.row3, text='OCR', command=(lambda: ocr_only(self.filename.get())))
        self.b6.pack(side=RIGHT, padx=5, pady=5)

    def processIncoming(self):
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
                    self.wipe()
                    self.txt1.set('empty')
                    self.txt2.set('empty')
                    self.txt3.set('empty')
                    self.status1.configure(textvariable=self.txt1, fg='red')
                    self.status2.configure(textvariable=self.txt2, fg='red')
                    self.status3.configure(textvariable=self.txt3, fg='red')
                if msg == 'clear':
                    self.query.delete(0, 'end')
                if msg == "enter_to_search":
                    self.search(self.filename.get(), self.query.get(), self.queue)
            except queue.Empty:
                pass


class app:
    def __init__(self, root):
        self.queue = queue.Queue()
        self.root = root
        self.root.bind('<Return>', lambda e=self: self.queue.put("enter_to_search"))
        self.gui = GuiPart(self.root,
                           self.queue,
                           self.shot_and_ocr,
                           self.ocr_only,
                           self.search_query,
                           self.visualize,
                           self.wipe,
                           self.end_application,
                           "train"
                           )
        self.running = 1
        self.periodic_call()

    def periodic_call(self):
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        root.after(200, self.periodic_call)

    def end_application(self):
        self.running = 0

    # Business logic

    def choose_area(self, coords1, coords2):
        subprocess.call([command_move.format(coords1)], shell=True)
        subprocess.call([command_down], shell=True)
        subprocess.call([command_move.format(coords2)], shell=True)
        subprocess.call([command_up], shell=True)

    def screenshot_and_preprocess(self, filename, area):
        subprocess.call([screenshot_command.format(filename)], shell=True)
        if area == "train":
            self.choose_area(coords_train_1, coords_train_2)
        else:
            self.choose_area(coords_real_1, coords_real_2)
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

    def screenshot_answer(self, filename):
        subprocess.call(["scrot -s -q 100 output/question.png &"], shell=True)
        subprocess.call(["xdotool mousemove 20 200"], shell=True)
        subprocess.call(["xdotool mousedown 1"], shell=True)
        subprocess.call(["xdotool mousemove 370 320"], shell=True)
        subprocess.call(["xdotool mouseup 1"], shell=True)
        time.sleep(0.2)
        subprocess.call(["mogrify -negate -modulate 100,0 -resize 300% output/question.png"], shell=True)
        subprocess.call(["./textcleaner output/question.png output/question.png"], shell=True)
        subprocess.call(["tesseract -l rus+eng output/question.png output/question"], shell=True)

        with open("output/question.txt", "r+") as f:
            contents = f.readlines()
            f.seek(0)
            flag = False
            for line in contents:
                if ("Question" not in line) and (not flag):
                    line = line.replace('\n', ' ')
                    f.write(line)
                if "?" in line:
                    flag = True
            f.truncate()
            f.close()

    def ocr_only(self, filename):
        subprocess.call([ocr_command.format(filename, filename)], shell=True)

    def shot_and_ocr(self, filename, area):
        self.screenshot_and_preprocess(filename, area)
        self.screenshot_answer(filename)
        subprocess.call([ocr_command.format(filename, filename)], shell=True)

    def search_query(self, filename, input, queue):
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

            thread1 = threading.Thread(target=(lambda: self.perform_search(input, ans[0], result1, queue, "success1")))
            thread1.start()
            thread2 = threading.Thread(target=(lambda: self.perform_search(input, ans[1], result2, queue, "success2")))
            thread2.start()
            thread3 = threading.Thread(target=(lambda: self.perform_search(input, ans[2], result3, queue, "success3")))
            thread3.start()

            thread1.join()

            result1.close()
            result2.close()
            result3.close()
            f.close()

    @staticmethod
    def perform_search(input, query, result, queue, msg):
        subprocess.call(["BROWSER=w3m googler -C --np -n 15 " + input + " " + query], shell=True, stdout=result)
        queue.put(msg)

    def wipe(self):
        f1 = open("./output/show1.txt", "w")
        f2 = open("./output/show2.txt", "w")
        f3 = open("./output/show3.txt", "w")
        f1.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f1.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f2.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f2.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f3.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f3.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        f1.close()
        f2.close()
        f3.close()

    def visualize(self, filename, query):

        keywords = query.split(" ")

        with open(filename + ".txt", "r") as f:
            contents = f.read()
            ans = contents.split("\n")
        f.close()

        show1 = open("./output/show1.txt", "w", encoding="utf-8")
        show2 = open("./output/show2.txt", "w", encoding="utf-8")
        show3 = open("./output/show3.txt", "w", encoding="utf-8")

        result1 = open("./output/result1.txt", "r", encoding="utf-8")
        result2 = open("./output/result2.txt", "r", encoding="utf-8")
        result3 = open("./output/result3.txt", "r", encoding="utf-8")

        lines1 = result1.readlines()
        lines2 = result2.readlines()
        lines3 = result3.readlines()

        result1.close()
        result2.close()
        result3.close()

        count = 0

        for line in lines1:
            if "http://" not in line and "https://" not in line:
                line = self.highlight_digits(line)
                for keyword in keywords:
                    res = self.highlight_keywords(line, keyword, "\033[91m")
                    line = res[0]
                    count = count + res[1]
                for answer in ans:
                    res = self.highlight_keywords(line, answer, "\033[95m")
                    line = res[0]
                    count = count + res[1]
                show1.write(line)
        print(count)
        count = 0

        for line in lines2:
            if "http://" not in line and "https://" not in line:
                line = self.highlight_digits(line)
                for keyword in keywords:
                    res = self.highlight_keywords(line, keyword, "\033[91m")
                    line = res[0]
                    count = count + res[1]
                for answer in ans:
                    res = self.highlight_keywords(line, answer, "\033[95m")
                    line = res[0]
                    count = count + res[1]
                show2.write(line)
        print(count)
        count = 0

        for line in lines3:
            if "http://" not in line and "https://" not in line:
                line = self.highlight_digits(line)
                for keyword in keywords:
                    res = self.highlight_keywords(line, keyword, "\033[91m")
                    line = res[0]
                    count = count + res[1]
                for answer in ans:
                    res = self.highlight_keywords(line, answer, "\033[95m")
                    line = res[0]
                    count = count + res[1]
                show3.write(line)
        print(count)

        show1.close()
        show2.close()
        show3.close()

    @staticmethod
    def highlight_keywords(text, keyword, color):
        replacement = color + keyword + "\033[39m"
        text = re.subn(re.escape(keyword), replacement, text, flags=re.I)
        return text

    @staticmethod
    def highlight_digits(text):
        keywords = re.findall("\d\d\d", text)
        # keywords = keywords + re.findall("\d\d\d", text)
        for keyword in keywords:
            replacement = "\033[92m" + keyword + "\033[39m"
            text = re.sub(re.escape(keyword), replacement, text, flags=re.I)
        return text


if __name__ == '__main__':
    root = Tk()
    root.title("Клевер")
    app(root)
    root.mainloop()
