"""截圖文字辨識模組"""
import easyocr
import numpy as np
from PIL import Image

_reader = None


def get_reader():
    """懶載入 OCR reader（第一次用才載入，避免啟動慢）"""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["ch_tra", "en"], gpu=False, verbose=False)
    return _reader


def extract_text_from_image(image) -> str:
    """從圖片中提取文字"""
    reader = get_reader()

    # 轉成 numpy array
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image

    results = reader.readtext(img_array)

    # 按照位置排序（上到下，左到右）
    results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))

    # 組合文字
    lines = []
    for bbox, text, confidence in results:
        if confidence > 0.3:  # 過濾低信心的結果
            lines.append(text)

    return "\n".join(lines)
