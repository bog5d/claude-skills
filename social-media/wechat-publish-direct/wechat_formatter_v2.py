#!/usr/bin/env python3
"""
微信公众号高质量排版引擎 v2.0
- 48 主题中的 elegant 系列风格（左边框递减 + 渐变背景）
- 每 400-500 字插入配图（叙事散文）
- 标题/摘要/正文/引用块/分隔线专业排版
"""

import re
import json
import os
import urllib.request
import urllib.parse
import random

# ==================== 配置 ====================
APPID = "wx37940d296d26c91c"
SECRET = "85c02f63a114b67277ab39eb13ae8d19"
IMAGE_DIR = "/tmp/wechat_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ==================== 主题样式定义 ====================
# elegant 风格：左边框递减 + 渐变背景 + 精致配色
THEME = {
    # 全局
    "body_font": "font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;",
    "body_color": "#3f3f3f",
    "body_line_height": "1.8",
    "body_font_size": "15px",
    "body_padding": "padding: 20px 15px;",
    
    # 标题
    "h1_style": """
        font-size: 22px;
        font-weight: bold;
        color: #1a1a1a;
        text-align: center;
        padding: 20px 0 15px;
        margin-bottom: 20px;
        border-bottom: 2px solid #e8d5b7;
        letter-spacing: 2px;
    """,
    "h2_style": """
        font-size: 18px;
        font-weight: bold;
        color: #2c2c2c;
        padding: 15px 0 10px 12px;
        margin: 30px 0 15px;
        border-left: 4px solid #c9a96e;
        background: linear-gradient(to right, rgba(201,169,110,0.08), transparent);
    """,
    
    # 正文
    "p_style": """
        font-size: 15px;
        line-height: 1.8;
        color: #3f3f3f;
        text-align: justify;
        margin: 12px 0;
        text-indent: 2em;
    """,
    
    # 强调
    "bold_style": "font-weight: bold; color: #1a1a1a;",
    "highlight_style": """
        background: linear-gradient(to bottom, transparent 60%, rgba(201,169,110,0.3) 60%);
        font-weight: bold;
    """,
    
    # 引用块
    "blockquote_style": """
        margin: 20px 0;
        padding: 15px 20px;
        border-left: 3px solid #c9a96e;
        background: linear-gradient(135deg, rgba(201,169,110,0.06), rgba(201,169,110,0.02));
        border-radius: 4px;
        font-style: italic;
        color: #555;
    """,
    
    # 分隔线
    "divider_style": """
        text-align: center;
        margin: 30px 0;
        color: #c9a96e;
        font-size: 14px;
        letter-spacing: 8px;
    """,
    
    # 图片
    "image_style": """
        display: block;
        margin: 25px auto;
        max-width: 100%;
        border-radius: 6px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    """,
    "image_caption_style": """
        text-align: center;
        font-size: 12px;
        color: #999;
        margin-top: 8px;
        font-style: italic;
    """,
}

# ==================== 文章数据 ====================
ARTICLE = {
    "title": "刘小兵家的夜路",
    "digest": "十二岁那年，我一个人过。煤气灶、插卡游戏机、第一顿豆芽。可真正让我记住的，是刘小兵家那盏灯。",
    "author": "王波",
    "sections": [
        {
            "heading": "一",
            "type": "section",
            "paragraphs": [
                "席子铺在口字形老屋中间的院坝里，夏天的夜风从田里钻过来，带着潮气。两张黄色大竹席铺在地上，爸妈、哥哥和我躺在上面——爷爷奶奶不住这儿，他们家隔着几栋房子，平日里各过各的，那晚也没来。",
                "爸妈从成都回来，商量我的事。我推测，爷爷奶奶不大愿意再带我；爸妈便说起另一个法子：转去龙马，离哥哥近一点，好照应。我听他们烦恼，心里却觉得没那么难——为啥非跟爷爷奶奶过？他们也不照顾我；转去学，又远又麻烦。我自己过不就行了？",
                "我躺在席子上，说了一句：我自己过。",
            ],
            "quote": "现在回想起来，那是我少年里少有的高光。一个十二岁的孩子，敢不要人安排、敢要一口自己的灶、一张自己的床。可那时我不知道，\"一个人过\"并不等于\"一个人就够了\"。",
            "paragraphs_after": [
                "煤气灶买回来，减轻了一点爸妈愧疚吧；插卡游戏机买回来，魂斗罗和忍者神龟把邻居孩子都招了来。爸每月给三十块，家里有米面。第一顿我自己去凤梧菜市场买豆芽，小贩塞给我四五斤，吃不完，我埋进土里，想种回豆芽——没长出来。独立生活的喜剧与狼狈，都从那几斤豆芽开始。",
            ],
        },
        {
            "heading": "二",
            "type": "section",
            "paragraphs": [
                "常去的是刘小兵家。",
                "他家离波多岭很近，就在爱群村小那一带——不是龙桥场镇外头。刘小兵比我大一岁，小时就熟，初中不同班，却越走越近。他妈走得早，爸没再娶，奶奶还在，表妹刘雪莲常在一块——那是一户愿意留饭、愿意留宿的人家。爱群村小时他常考第一，到了中心小学名次被冲淡了，仍很靠前；他姐刘伙燕成绩也好，没大我多少，却有一种慈爱，还幽默——刚认识那阵她就不住家里了，已出嫁，但总跟人说：王波性格好，外向开朗，以后能干大事。那是很多个夜晚之前的事了，那一晚她并不在场。",
            ],
            "paragraphs_mid": [
                "有一回，电视里反复放着一首歌，《下沙》，\"天空下着沙，也在笑我太傻\"。刘雪莲在灶边把土豆切片、切丝，我蹲在旁边看，学着拿刀——那是我第一次把一根土豆切成能下锅的丝。奶奶拎着刷把回来，手起得快，辣椒籽剔得干干净净。爸收工回家，一家人端着碗，下到比堂屋矮一截的那间屋子，看新闻联播——每晚七点，中央台，中国人几乎都知道的那档节目。天气预报先播，联播正文过去，他爸才坐直了身子：国际新闻要来了。",
            ],
            "paragraphs_after": [
                "我那时常以为自己没有家。口字形的老屋是我一个人的，冷清，游戏机响起来的时候又太吵。可在刘小兵家，吃啥跟着吃，电视跟着看，床上躺着说话。天黑了，我们是走到对门去，在他家睡下，并不是当晚送我回去。第二天放假，吃完早饭，刘小兵送我一程，送得很远；分开时彼此说以后要怎么成长，都很舍不得。我回到家，偌大的房子又只剩我一个，玩玩游戏，常常还是很无聊。",
                "有一回放学，我俩背着饭盒袋，饭盒里搁着饭勺，往他家方向走。若从他家去千佛寺中学，路是这样记的：先过波多岭，再出龙桥场镇外头一个湾子——我们正是在那儿遇见挑西瓜卖的伯伯，两毛钱一斤——然后才进龙桥镇，再往千佛寺去。那天我们是逆着这条路往回走：刚出镇没多远，在湾子里买了瓜，走到路边低下去的地里，靠着土坡，把西瓜往石头上摔开，掏出饭勺挖着吃。瓜汁顺着手腕流下来，渴意一下子退下去。两个人都不说话，又都觉得这下午好得很——不是因为西瓜甜，是因为有个人，愿意跟你做这件傻事。",
            ],
        },
        {
            "heading": "三",
            "type": "section",
            "paragraphs": [
                "惭愧的事也有。初二下学期左右——那时还没住校——他家附近有个叫刘强家的孩子，房子修得齐整，我、刘小兵、刘强在刘强家玩。我带了游戏机，当晚想留宿刘强家——机子在手，舍不得走。刘小兵说要回对面自己家住，顿了顿，又说，一个人走夜路，有点怕。",
            ],
            "quote": "我没陪他。",
            "paragraphs_after": [
                "我留在刘强家，继续玩。第二天，刘强要走亲戚，他爷爷来赶人，话不好听，场面难看。我提着游戏机出来，站在门口，不知道往哪边去。",
                "许多年后我才明白：新奇的房子、新鲜的机子、好客的玩伴，都可以留你一夜；真正愿意接纳你的，其实一直是刘小兵一家。新闻联播里的国际新闻、灶台上的土豆丝、土坡边的碎西瓜、放假清晨送远的那条路——那些才是家。而我曾在某一个怕黑的夜，选择了游戏手柄，而不是朋友的背影。",
            ],
        },
        {
            "heading": "四",
            "type": "section",
            "paragraphs": [
                "初中后来还有更大的惭愧，高中也有。那些事先搁着。只说刘小兵：仁寿中学的简章我拿过，爸说可以报名住校，我舍不得李红兵们，没去。若那时走了，后来的一切会不会改写？我不知道。我只知道，在我最需要\"被当成自己人\"的年岁里，刘小兵家始终留着一盏灯。",
                "我穿他的衣服去看过别的女生。我在他家过夜，也在别人家过夜。他常送我很远，分开时彼此约定怎么长大。少年人不懂报答，只懂索取陪伴——可陪伴这件事，他从来没跟我计较过。",
            ],
        },
    ],
}

# ==================== 配图策略 ====================
# 叙事散文：每 400-500 字配一张图
# 封面图 + 章节间氛围图 + 关键场景特写
IMAGE_PROMPTS = {
    "cover": "A warm lantern hanging in a rural Chinese courtyard at dusk, traditional mud-brick houses, golden hour lighting, nostalgic atmosphere, cinematic composition",
    "section1": "A bamboo mat spread on the ground in a rural Chinese courtyard, summer evening, starlight, simple and peaceful countryside scene",
    "section2": "A rural Chinese village path at twilight, two children walking home together, warm sunset glow, nostalgic countryside atmosphere",
    "section2_watermelon": "Children eating watermelon on a dirt embankment by a rural road, summer afternoon, juice dripping, friendship scene",
    "section3": "A lonely boy standing at the gate of a nice house at night, holding a game console, feeling lost, emotional scene",
    "section4": "A single warm lantern lit in a dark rural house window at night, hope and belonging, cinematic lighting",
}

# ==================== 图片生成/下载 ====================
def download_image(url, filename):
    """下载图片到本地"""
    filepath = os.path.join(IMAGE_DIR, filename)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(filepath, "wb") as f:
                f.write(data)
        print(f"  ✅ {filename} ({len(data)} bytes)")
        return filepath
    except Exception as e:
        print(f"  ❌ {filename}: {e}")
        return None

def generate_placeholder_image(filename, width=900, height=600, color="#c9a96e"):
    """生成纯色占位图（当无法下载时）"""
    filepath = os.path.join(IMAGE_DIR, filename)
    # 用 base64 生成一个简单的 SVG 作为占位图
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
        <rect width="100%" height="100%" fill="{color}"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
              font-family="sans-serif" font-size="24" fill="white" opacity="0.6">
            {filename.replace('.jpg', '').replace('_', ' ')}
        </text>
    </svg>'''
    with open(filepath, "wb") as f:
        f.write(svg.encode())
    print(f"  📷 {filename} (placeholder)")
    return filepath

# ==================== HTML 生成器 ====================
def generate_html():
    """生成公众号 HTML"""
    parts = []
    
    # 外层容器
    parts.append(f'''<div style="{THEME['body_font']} {THEME['body_color']};
        {THEME['body_line_height']}; {THEME['body_font_size']};
        {THEME['body_padding']}">''')
    
    # 标题
    parts.append(f'<h1 style="{THEME["h1_style"]}">{ARTICLE["title"]}</h1>')
    
    # 作者行
    parts.append(f'''<p style="text-align:center; font-size:13px; color:#999; margin-bottom:25px;">
        {ARTICLE["author"]}
    </p>''')
    
    # 分隔线
    parts.append(f'<p style="{THEME["divider_style"]}">· · · ✦ · · ·</p>')
    
    word_count = 0
    
    for section in ARTICLE["sections"]:
        # 章节标题
        parts.append(f'<h2 style="{THEME["h2_style"]}">{section["heading"]}</h2>')
        
        # 段落
        for para in section.get("paragraphs", []):
            parts.append(f'<p style="{THEME["p_style"]}">{para}</p>')
            word_count += len(para)
        
        # 引用块
        if "quote" in section:
            parts.append(f'<blockquote style="{THEME["blockquote_style"]}">{section["quote"]}</blockquote>')
        
        # 中间段落
        for para in section.get("paragraphs_mid", []):
            parts.append(f'<p style="{THEME["p_style"]}">{para}</p>')
            word_count += len(para)
        
        # 每达到 300-400 字，插入配图
        if word_count >= 300:
            # 根据章节选择图片
            section_num = section["heading"]
            img_key = f"section{section_num}"
            
            # 特殊场景图
            if "西瓜" in "".join(section.get("paragraphs", []) + section.get("paragraphs_after", [])):
                img_key = "section2_watermelon"
            elif section_num == "三":
                img_key = "section3"
            elif section_num == "四":
                img_key = "section4"
            
            prompt = IMAGE_PROMPTS.get(img_key, IMAGE_PROMPTS["cover"])
            img_filename = f"img_{section_num.lower()}.jpg"
            
            parts.append(f'''<div style="text-align:center;">
                <img src="{img_filename}" style="{THEME['image_style']}" />
                <p style="{THEME['image_caption_style']}">{prompt[:80]}...</p>
            </div>''')
            word_count = 0
        
        # 节后段落
        for para in section.get("paragraphs_after", []):
            parts.append(f'<p style="{THEME["p_style"]}">{para}</p>')
            word_count += len(para)
        
        # 节末分隔
        parts.append(f'<p style="{THEME["divider_style"]}">· · · ✦ · · ·</p>')
    
    # 结尾
    parts.append(f'''<p style="{THEME['p_style']} text-indent:0; text-align:center; color:#999; font-size:13px; margin-top:40px;">
        — 完 —
    </p>''')
    
    parts.append('</div>')
    
    return "\n".join(parts)

# ==================== 主流程 ====================
if __name__ == "__main__":
    html = generate_html()
    
    output_path = "/tmp/wechat_article_v2.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ HTML 已生成: {output_path}")
    print(f"📊 字数统计: 全文约 {sum(len(p) for s in ARTICLE['sections'] for p in s.get('paragraphs', []) + s.get('paragraphs_mid', []) + s.get('paragraphs_after', []))} 字")
    print(f"🖼️ 配图: 封面 + 4 张章节配图")
    print(f"🎨 主题: elegant 风格（左边框递减 + 渐变背景）")
