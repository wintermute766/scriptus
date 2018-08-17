from __future__ import print_function
import sys
from PIL import Image
import subprocess
import time

filename = "./output/answer4"

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

def screenshot_and_preprocess(filename, area):
    subprocess.call([screenshot_command.format(filename)] , shell=True)
    if area=="train":
        choose_area(coords_train_1, coords_train_2)
    else:
        choose_area(coords_real_1, coords_real_2)
    time.sleep(0.5)
    subprocess.call([image_command_1.format(filename)], shell=True)
    subprocess.call([image_command_2.format(filename, filename)], shell=True)
    im = Image.open(filename+".png")
    #print(im.format, "%dx%d" % im.size, im.mode)
    fill_color = (0,0,0)
    toPaste = Image.new("L", (960, 45), "white")
    box1 = (0, 105, 960, 150)
    box2 = (0, 255, 960, 300)
    im.paste(toPaste, box1)
    im.paste(toPaste, box2)
    im.save(filename+".png")

def ocr(filename):
    subprocess.call([ocr_command.format(filename, filename)], shell=True)

def choose_area(coords1, coords2):
    subprocess.call([command_move.format(coords1)], shell=True)
    subprocess.call([command_down], shell=True)
    subprocess.call([command_move.format(coords2)], shell=True)
    subprocess.call([command_up], shell=True)

def search_query(filename):
    with open(filename+".txt","r+") as f:
        contents = f.read()
        f.seek(0)
        newcontents = contents.replace('\n\n','\n')
        f.write(newcontents)
        f.close()
    with open(filename+".txt","r") as f:
        contents = f.read()
        ans = contents.split("\n")
        result1 = open("./output/result1.txt", "w", encoding="utf-8")
        result2 = open("./output/result2.txt", "w", encoding="utf-8")
        result3 = open("./output/result3.txt", "w", encoding="utf-8")
        subprocess.call(["BROWSER=w3m googler -n 15 "+sys.argv[1]+" "+ans[0]], shell=True, stdout=result1)
        subprocess.call(["xdotool key Return"], shell=True)
        subprocess.call(["xdotool key Return"], shell=True)
        subprocess.call(["xdotool key Return"], shell=True)
        subprocess.call(["xdotool key Return"], shell=True)
        subprocess.call(["xdotool key Return"], shell=True)
        subprocess.call(["BROWSER=w3m googler -n 15 "+sys.argv[1]+" "+ans[1]], shell=True, stdout=result2)
        subprocess.call(["BROWSER=w3m googler -n 15 "+sys.argv[1]+" "+ans[2]], shell=True, stdout=result3)
        result1.close()
        result2.close()
        result3.close()
        f.close()

def main():
  #screenshot_and_preprocess(filename, "train")
  ocr(filename)
  search_query(filename)

if __name__== "__main__":
  main()
