python3 script.py "bioshock" 2>/dev/null

#!/bin/bash
# Dependencies: tesseract-ocr imagemagick scrot

SCR_IMG=`mktemp`
trap "rm $SCR_IMG*" EXIT

scrot -s $SCR_IMG.png -q 100
# increase quality with option -q from default 75 to 100
# Typo "$SCR_IMG.png000" does not continue with same name.

mogrify -modulate 100,0 -resize 400% $SCR_IMG.png
#should increase detection rate

tesseract -l rus $SCR_IMG.png $SCR_IMG &> /dev/null
cat $SCR_IMG.txt
exit

'''
subprocess.call(["scrot -s -q 100 question.png &"] , shell=True)

subprocess.call(["xdotool mousemove 20 200"], shell=True)
subprocess.call(["xdotool mousedown 1"], shell=True)
subprocess.call(["xdotool mousemove 400 350"], shell=True)
subprocess.call(["xdotool mouseup 1"], shell=True)

time.sleep(0.5)

subprocess.call(["mogrify -modulate 100,0 -resize 300% question.png"], shell=True)

subprocess.call(["tesseract -l rus+eng question.png question"], shell=True)

with open("question.txt","r+") as f:
    contents = f.readlines()
    f.seek(0)
    flag = False
    for line in contents:
        if ("Question" not in line) and (not flag):
            f.write(line)
        if ("?" in line):
            flag = True
    f.truncate()
    f.close()

with open("question.txt","r+") as f:
    contents = f.read()
    f.seek(0)
    newcontents = contents.replace('\n',' ')
    f.write(newcontents)
    print newcontents
    f.close()
'''
