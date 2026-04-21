
import jieba
from matplotlib import pyplot as plt
from wordcloud import WordCloud
from PIL import Image, ImageFilter
import numpy as np
import sqlite3
import random
import cv2

# ---------- 数据库读取与分词（不变）----------
con = sqlite3.connect('movies.db')
cur = con.cursor()
data = cur.execute('select instroduction from top250')
text = ''
for i in data:
    text += i[0]
cur.close()
con.close()

text = text.replace(' ', '')
cut = jieba.cut(text)
string = ' '.join(cut)


# ---------- 生成精确的人物 mask（白色为人）----------
def create_person_mask(image_path, target_width=2400, blur_ksize=5, close_ksize=7):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape[:2]
    if w != target_width:
        ratio = target_width / w
        new_h = int(h * ratio)
        img = cv2.resize(img, (target_width, new_h), interpolation=cv2.INTER_AREA)

    blurred = cv2.GaussianBlur(img, (blur_ksize, blur_ksize), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((close_ksize, close_ksize), np.uint8)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(closed)
    cv2.drawContours(mask, contours, -1, 255, cv2.FILLED)
    return mask, img  # 同时返回缩放后的原图


mask, original_gray = create_person_mask('./static/assets/img/ink.png', target_width=2400)
#mask, original_gray = create_person_mask('./static/assets/img/warrior.jpg', target_width=2400)

# ---------- 颜色函数（不变）----------
def warhammer_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    blue_shades = [(10, 30, 80), (20, 60, 140), (40, 90, 200), (80, 140, 255)]
    gold_shades = [(212, 175, 55), (255, 215, 0), (184, 134, 11)]
    if random.random() < 0.1:
        color = random.choice(gold_shades)
    else:
        color = random.choice(blue_shades)
    return f"rgb({color[0]}, {color[1]}, {color[2]})"


# ---------- 生成全幅词云（无 mask 限制）----------
wc = WordCloud(
    background_color='white',
    # 不传入 mask，让词云填满整个画布
    width=mask.shape[1],
    height=mask.shape[0],
    max_words=8000,
    min_font_size=35,          # 🔼 从 18 提高到 35，小字直接变大
    max_font_size=400,         # 🔼 从 300 提高到 400，大字上限更高
    relative_scaling=0.2,      # 🔽 从 0.6 降低到 0.2，让所有词的字号更接近上限
    color_func=warhammer_color_func,
    random_state=42,
    collocations=False,
    font_path='FZSTK.TTF'
)
wc.generate(string)

# 将词云转换为 numpy 数组（RGB）
wordcloud_img = np.array(wc.to_image())  # shape: (H, W, 3)

# ---------- 合成：人物区域显示原图细节，背景显示词云 ----------
# 将 mask 归一化到 [0, 1] 并转为 3 通道
mask_3ch = np.stack([mask / 255.0] * 3, axis=-1)

# 原图灰度转为三通道伪彩色（或保留灰度），可加一点蓝色调增强质感
gray_3ch = np.stack([original_gray] * 3, axis=-1) / 255.0
# 可选：轻微调色，让线条更明显（反色或增强对比度）
# gray_3ch = 1.0 - gray_3ch   # 若想黑底白线

# 合成公式：最终图像 = 词云 * (1 - mask) + 原图 * mask
composite = wordcloud_img / 255.0 * (1 - mask_3ch) + gray_3ch * mask_3ch
composite = (composite * 255).astype(np.uint8)

# ---------- 保存结果 ----------
plt.figure(figsize=(16, 10), dpi=300)
plt.imshow(composite)
plt.axis('off')
plt.tight_layout(pad=0)
plt.savefig('./static/assets/img/word.png', dpi=600, bbox_inches='tight', pad_inches=0)
# plt.savefig('./static/assets/img/coolwarrior.png', dpi=600, bbox_inches='tight', pad_inches=0)
plt.close()
