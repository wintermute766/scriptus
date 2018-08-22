# -*- coding: utf-8 -*-
import pathlib
import queue
import subprocess
import threading
import time
from tkinter import *

import pytesseract
from PIL import Image

# import nltk
# nltk.download("stopwords")
from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation

coords_real_1 = "40 320"
coords_real_2 = "300 460"
coords_train_1 = "40 340"
coords_train_2 = "300 480"

coords_q_real_1 = "20 180"
coords_q_real_2 = "370 300"
coords_q_train_1 = "20 200"
coords_q_train_2 = "370 320"

command_move = "xdotool mousemove {}"
command_down = "xdotool mousedown 1"
command_up = "xdotool mouseup 1"

screenshot_command = "scrot -s -q 100 {}.png &"
image_command_1 = "mogrify -modulate 100,0 -resize 300% {}.png"
image_command_2 = "./textcleaner {}.png {}.png"

mystem = Mystem()
russian_stopwords = stopwords.words("russian")


def preprocess_text(text):
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords
              and token != " "
              and token.strip() not in punctuation]
    text = " ".join(tokens)

    return text


class GuiPart:
    def __init__(self, root, queue, ocr, ocr_only, search, auto_search, visualize, wipe, end_command, area):

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

        self.b1 = Button(self.row2, text='Screenshot', command=(lambda: ocr(self.filename.get(), area, queue)))
        self.b1.pack(side=LEFT, padx=5, pady=5)

        self.b2 = Button(self.row2, text='Search', command=(lambda: search(self.filename.get(), self.query.get(), queue)))
        self.b2.pack(side=LEFT, padx=5, pady=5)

        self.b3 = Button(self.row2, text='Show', command=(lambda: visualize(self.filename.get(), self.query.get())))
        self.b3.pack(side=RIGHT, padx=5, pady=5)

        self.b6 = Button(self.row2, text='OCR', command=(lambda: ocr_only(self.filename.get(), queue)))
        self.b6.pack(side=RIGHT, padx=5, pady=5)

        self.b8 = Button(self.row2, text='Auto', command=(lambda: auto_search(self.filename.get(), area, queue)))
        self.b8.pack(side=LEFT, padx=5, pady=5)

        # row 3

        self.row3 = Frame(root)
        self.row3.pack(fill=X, padx=5, pady=5)

        self.b4 = Button(self.row3, text='Clear files', command=(lambda: queue.put("wipe")))
        self.b4.pack(side=LEFT, padx=5, pady=5)

        self.b7 = Button(self.row3, text='Exit', command=end_command)
        self.b7.pack(side=RIGHT, padx=5, pady=5)

        self.b5 = Button(self.row3, text='Clear text', command=(lambda: queue.put("clear")))
        self.b5.pack(side=LEFT, padx=5, pady=5)

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
                if msg == "ocr_success":
                    pass
            except queue.Empty:
                pass


class app:
    def __init__(self, root, area):
        self.queue = queue.Queue()
        self.root = root
        self.root.bind('<Return>', lambda e=self: self.queue.put("enter_to_search"))
        self.gui = GuiPart(self.root,
                           self.queue,
                           self.do_shot_and_ocr,
                           self.do_ocr_only,
                           self.do_search,
                           self.do_auto_search,
                           self.do_visualize,
                           self.do_wipe,
                           self.end_application,
                           area
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

    @staticmethod
    def choose_area(coords1, coords2):
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
        time.sleep(0.2)
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

    def screenshot_answer(self, filename, area):
        subprocess.call([screenshot_command.format(filename)], shell=True)
        if area == "train":
            self.choose_area(coords_q_train_1, coords_q_train_2)
        else:
            self.choose_area(coords_q_real_1, coords_q_real_2)
        time.sleep(0.2)
        subprocess.call(["mogrify -negate -modulate 100,0 -resize 300% " + filename + ".png"], shell=True)
        subprocess.call([image_command_2.format(filename, filename)], shell=True)
        text = pytesseract.image_to_string(Image.open(filename + ".png"), lang='rus+eng')
        lines = text.split("\n")
        question = ""
        with open(filename + ".txt", "w") as f:
            flag = False
            for line in lines:
                if ("Question" not in line) and (not flag):
                    question = question + " " + line
                if "?" in line:
                    flag = True
            f.truncate()
            f.write(question)

    def do_ocr_only(self, filename, queue):
        self.ocr(filename, queue)

    def do_shot_and_ocr(self, filename, area, queue):
        self.screenshot_and_preprocess(filename, area)
        self.ocr(filename, queue)

    @staticmethod
    def ocr(filename, queue):
        text = pytesseract.image_to_string(Image.open(filename + ".png"), lang='rus+eng')
        with open(filename + ".txt", "w") as f:
            f.write(text)
        with open(filename + ".txt", "r") as f:
            contents = f.read()
        with open(filename + ".txt", "w") as f:
            contents = re.sub(re.escape("\n\n"), "\n", contents, flags=re.I)
            contents = re.sub(re.escape("\n \n"), "\n", contents, flags=re.I)
            f.write(contents)
            queue.put("ocr_success")

    def do_search(self, filename, input, queue):
        self.search_query(filename, input, queue)
        self.do_visualize(filename, input)

    def do_auto_search(self, filename, area, queue):
        time1 = time.time()
        self.do_shot_and_ocr(filename, area, queue)
        self.screenshot_answer("output/question", area)
        with open("output/question.txt", "r") as f:
            contents = f.read()
            contents = preprocess_text(contents)
        self.search_query(filename, contents, queue)
        self.do_visualize(filename, contents)
        time2 = time.time()
        print(time2 - time1)

    def search_query(self, filename, input, queue):
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
        thread2.join()
        result2.close()
        thread3.join()
        result3.close()

    @staticmethod
    def perform_search(input, query, file, queue, msg):
        subprocess.call(["BROWSER=w3m googler -C --np -n 10 " + input + " " + query], shell=True, stdout=file)
        queue.put(msg)

    @staticmethod
    def do_wipe():
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

    def do_visualize(self, filename, input):

        if input == "":
            keywords = " "
        else:
            keywords = input.split(" ")
        keywords1 = []
        for keyword in keywords:
            if keyword.isalpha() or keyword.isnumeric():
                keywords1.append(keyword)
        keywords = keywords1
        print(keywords)

        with open(filename + ".txt", "r") as f:
            contents = f.read()
            contents = contents.lower()
            ans = contents.split("\n")
        ans = ans[:3]
        regex = re.compile('[,\.!?«»]')
        ans[0] = regex.sub('', ans[0])
        ans[1] = regex.sub('', ans[1])
        ans[2] = regex.sub('', ans[2])
        print(ans)

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

        count = [0, 0, 0]

        self.highlight(ans, keywords, lines1, show1, count)
        self.highlight(ans, keywords, lines2, show2, count)
        self.highlight(ans, keywords, lines3, show3, count)

        print(count)

        show1.close()
        show2.close()
        show3.close()

    def highlight(self, ans, keywords, lines, show, count):
        for line in lines:
            if "http://" not in line and "https://" not in line:
                if keywords != " ":
                    for keyword in keywords:
                        res = self.highlight_keywords(line, keyword, "\033[91m")
                        line = res[0]
                        # count[0] = count[0] + res[1]
                for answer in ans:
                    res = self.highlight_keywords(line, answer, "\033[95m")
                    line = res[0]
                    count[ans.index(answer)] = count[ans.index(answer)] + res[1]
                line = self.highlight_digits(line)
                show.write(line)

    @staticmethod
    def highlight_keywords(text, keyword, color):
        replacement = color + keyword + "\033[39m"
        '''
        if keyword.isnumeric():
            text = re.subn(r"\b%s\b" % re.escape(keyword), replacement, text, flags=re.I)
        else:
            text = re.subn(re.escape(keyword), replacement, text, flags=re.I)
        '''
        text = re.subn(r"\b%s\b" % re.escape(keyword), replacement, text, flags=re.I)
        return text

    @staticmethod
    def highlight_digits(text):
        keywords = re.findall(r"\d\d", text)
        keywords = keywords + re.findall(r"\d", text)
        keywords = keywords + re.findall(r"\d\d\d", text)
        keywords = keywords + re.findall(r"\d\d\d\d", text)
        keywords = keywords + re.findall(r"\d\d\d\d\d", text)
        keywords = keywords + re.findall(r"\d\d\d\d\d\d", text)
        keywords = keywords + re.findall(r"\d\d\d\d\d\d\d", text)
        for keyword in keywords:
            replacement = "\033[92m" + keyword + "\033[39m"
            text = re.sub(r"\b%s\b" % re.escape(keyword), replacement, text, flags=re.I)
        return text


if __name__ == '__main__':
    pathlib.Path("output").mkdir(parents=True, exist_ok=True)
    root = Tk()
    root.title("Клевер")
    app(root, "train")
    root.mainloop()
