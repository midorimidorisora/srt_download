from html import unescape
from xml.etree import ElementTree
from flask import Flask, render_template, request,make_response
from pytube import YouTube
from pykakasi import kakasi
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def get_transcript(url):
    yt = YouTube(url)
    caption = yt.captions['a.ja']
    transcript = caption.generate_srt_captions()
    return transcript

def xml_caption_to_srt(self, xml_captions: str) -> str:
        """Convert xml caption tracks to "SubRip Subtitle (srt)".

        :param str xml_captions:
        XML formatted caption tracks.
        """
        segments = []
        root = ElementTree.fromstring(xml_captions)
        i=0
        for child in list(root.iter("body"))[0]:
            if child.tag == 'p':
                caption = ''
                if len(list(child))==0:
                    # instead of 'continue'
                    caption = child.text
                for s in list(child):
                    if s.tag == 's':
                        caption += ' ' + s.text
                caption = unescape(caption.replace("\n", " ").replace("  ", " "),)
                try:
                    duration = float(child.attrib["d"])/1000.0
                except KeyError:
                    duration = 0.0
                start = float(child.attrib["t"])/1000.0
                end = start + duration
                sequence_number = i + 1  # convert from 0-indexed to 1.
                line = "{seq}\n{start} --> {end}\n{text}\n".format(
                    seq=sequence_number,
                    start=self.float_to_srt_time_format(start),
                    end=self.float_to_srt_time_format(end),
                    text=caption,
                )
                segments.append(line)
                i += 1
        return "\n".join(segments).strip()

# 轉換日文為假名
def convert_japanese_to_kana(text: str) -> str:
    kakasi_instance = kakasi()
    kakasi_instance.setMode('J', 'H')
    conv = kakasi_instance.getConverter()
    result = ""
    for c in text:
        if ord(c) >= 0x4e00 and ord(c) <= 0x9fff:
            result += "[" + conv.do(c) + "]"
        else:
            result += c
    return result

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    # 取得影片標題
    video = YouTube(url)
    title = video.title

    transcript = get_transcript(url)
    #transcript = convert_japanese_to_kana(transcript)
    response = make_response(transcript)
  
    # 移除行號和時間，只保留字幕內容
    srt = response.data.decode("utf-8").split("\n")
    lines = []
    for i in range(0, len(srt), 4):
        #lines.append(srt[i+2])
        line = srt[i+2].strip()  # 移除前后空格
        if line:  # 判断是否为空白行
            lines.append(line)
    response.data = "\n".join(lines)
    
    response.headers.set("Content-Disposition", "attachment", filename=title + ".txt")
    response.headers.set("Content-Type", "text/plain")
    return response

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='127.0.0.1',port=5001)