"""派对主题视觉预设：不同类目 -> 不同配色 / 气质，用于方案卡 HTML。

每个主题包含：emoji、标题、标语、背景渐变、卡片底色、主色、强调色、正文色、
弱化色、标签底色。新增类目时往 THEMES 里加一项即可。
"""

THEMES = {
    "生日类派对": {
        "emoji": "🎂", "title": "生日派对", "tagline": "生日快乐，麦麦陪你过生日",
        "bg": "linear-gradient(135deg,#FF9A9E 0%,#FECFEF 100%)",
        "card": "#FFFFFF", "primary": "#FF5C8A", "accent": "#FFD166",
        "text": "#5A2A41", "muted": "#9A6B7C", "chip": "#FFE3EC",
    },
    "主题类派对": {
        "emoji": "🎪", "title": "主题派对", "tagline": "主题派对，一起嗨翻天",
        "bg": "linear-gradient(135deg,#A18CD1 0%,#FBC2EB 100%)",
        "card": "#FFFFFF", "primary": "#7C3AED", "accent": "#38BDF8",
        "text": "#3B0764", "muted": "#7C6AA6", "chip": "#EDE9FE",
    },
    "品鉴会": {
        "emoji": "🍷", "title": "品鉴会", "tagline": "品鉴之约，风味之旅",
        "bg": "linear-gradient(135deg,#232526 0%,#414345 100%)",
        "card": "#2A2D31", "primary": "#D4AF37", "accent": "#C0A062",
        "text": "#F5F0E1", "muted": "#B8B0A0", "chip": "#3A3D42",
    },
    "读书会": {
        "emoji": "📚", "title": "亲子读书会", "tagline": "共读时光，麦麦亲子读书会",
        "bg": "linear-gradient(135deg,#E0EAFC 0%,#CFDEF3 100%)",
        "card": "#FFFFFF", "primary": "#0E9F94", "accent": "#F59E0B",
        "text": "#134E4A", "muted": "#5B7F7C", "chip": "#D6F5F1",
    },
    "麦麦体验营": {
        "emoji": "🚀", "title": "麦麦体验营", "tagline": "探索体验，快乐成长",
        "bg": "linear-gradient(135deg,#43E97B 0%,#38F9D7 100%)",
        "card": "#FFFFFF", "primary": "#0E9F6E", "accent": "#FBBF24",
        "text": "#064E3B", "muted": "#4B7C6B", "chip": "#D7F5E6",
    },
}

DEFAULT_THEME = {
    "emoji": "🎉", "title": "麦麦派对", "tagline": "一句话，办一场麦当劳派对",
    "bg": "linear-gradient(135deg,#FFD194 0%,#FFB4A2 100%)",
    "card": "#FFFFFF", "primary": "#E8590C", "accent": "#F59F00",
    "text": "#5C2E0E", "muted": "#9C6644", "chip": "#FFE8CC",
}


def get_theme(category):
    """按类目取主题；未命中回退默认主题。"""
    return THEMES.get(category, DEFAULT_THEME)
