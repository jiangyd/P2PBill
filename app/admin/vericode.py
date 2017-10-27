from PIL import Image,ImageDraw,ImageFont,ImageFilter
import random
import os
 #随机码 默认长度=1
def random_code(lenght=1):
    code = ''
    for char in range(lenght):
        code += chr(random.randint(65,90))
    return code

 #随机颜色 默认颜色范围【1，255】
def random_color(s=1,e=255):
    return (random.randint(s,e),random.randint(s,e),random.randint(s,e))

 #生成验证码图片
 #length 验证码长度
 #width 图片宽度
 #height 图片高度
 #返回验证码和图片
def veri_code(lenght=4,width=160,height=34):
    #创建Image对象
    image = Image.new('RGB',(width,height),(255,255,255))
    #创建Font对象
    filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)),'ubuntu.ttf')
    print(filepath)
    font = ImageFont.truetype(filepath,32)
    #创建Draw对象
    draw = ImageDraw.Draw(image)
    #随机颜色填充每个像素
    for x in range(width):
        for y in range(height):
            draw.point((x,y),fill=random_color(64,255))
    #验证码
    code = random_code(lenght)
    #随机颜色验证码写到图片上
    for t in range(lenght):
        draw.text((40*t+5,5),code[t],font=font,fill=random_color(32,127))
    #模糊滤镜
    image = image.filter(ImageFilter.SMOOTH_MORE)
    return code,image
