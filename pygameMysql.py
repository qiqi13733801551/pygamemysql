import pygame
import sys
import pymysql
import time
import random
from pygame.locals import *
from datetime import timedelta  # 新增：导入timedelta处理时间差

# ---------------------- 全局配置 ----------------------
pygame.init()
WIDTH, HEIGHT = 820, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MySQL慢查询监控室 🕵️‍♂️")
clock = pygame.time.Clock()

# 关键：指定中文字体（Windows/macOS/Linux 路径不同）
try:
    mid_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 14)  # 14号字
    small_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 10) # 小号字
except:
    try:
        mid_font = pygame.font.Font("C:/Windows/Fonts/simsun.ttc", 14)
        small_font = pygame.font.Font("C:/Windows/Fonts/simsun.ttc", 10)
    except:
        mid_font = pygame.font.SysFont("simhei", 14)
        small_font = pygame.font.SysFont("simhei", 10)

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 69, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)          
YELLOW = (255, 255, 0)      
GRAY = (128, 128, 128)
LIGHT_GRAY = (220, 220, 220)

COFFEE_CUP = (102, 66, 40)  # RGB颜色值：红=102, 绿=66, 蓝=40

# 木纹色系
WOOD_DARK = (101, 67, 33)
WOOD_MID = (139, 69, 19)
WOOD_LIGHT = (160, 82, 45)

# 场景色系
TILE_BEIGE = (245, 245, 220)
TILE_GRAY = (200, 200, 200)
SOFA_PURPLE = (128, 20, 128)
SOFA_LIGHT = (148, 40, 148)
PLANT_GREEN = (34, 139, 34)
SCREEN_BLUE = (0, 50, 100)

# 角色色系（匹配图片风格）
CHAR_SKIN = (245, 222, 179)    # 肤色
CHAR_HAIR_NORMAL = (105, 105, 105)  # 正常头发（灰色，匹配图片）
CHAR_HAIR_ANGRY = (255, 0, 0)       # 发怒红头发
CHAR_CLOTHES = (100, 149, 237)      # 衣服色（钢蓝）
CHAR_EYES = (0, 0, 0)               # 眼睛颜色
CHAR_MOUTH = (139, 69, 19)          # 嘴巴颜色

# MySQL配置（修改为你的数据库信息）
MYSQL_CONFIG = {
    "host": "您的数据库连接地址",
    "user": "您的数据库用户名",
    "password": "您的数据库密码",
    "database": "您的数据库名称",
    "charset": "utf8mb4"
}

# ---------------------- 工具函数：安全颜色计算 ----------------------
def safe_color(color, offset):
    r = max(0, min(255, color[0] + offset))
    g = max(0, min(255, color[1] + offset))
    b = max(0, min(255, color[2] + offset))
    return (r, g, b)

# ---------------------- 新增工具函数：时间差转秒数 ----------------------
def timedelta_to_seconds(time_value):
    if isinstance(time_value, timedelta):
        return time_value.total_seconds()
    elif isinstance(time_value, (int, float)):
        return float(time_value)
    else:
        try:
            return float(time_value)
        except (ValueError, TypeError):
            return 0.0

# ---------------------- 像素纹理生成工具 ----------------------
def draw_wood_texture(surface, rect, color):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect)
    for i in range(0, h, 4):
        line_color = safe_color(color, -10) if i%8==0 else safe_color(color, +5)
        pygame.draw.line(surface, line_color, (x, y+i), (x+w, y+i), 1)
    for i in range(0, w, 20):
        for j in range(0, h, 15):
            node_color = safe_color(color, -15)
            pygame.draw.circle(surface, node_color, 
                             (x+i+random.randint(2,8), y+j+random.randint(2,8)), 1)

def draw_tile_texture(surface, rect, color):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect)
    tile_size = 20
    for i in range(x, x+w, tile_size):
        pygame.draw.line(surface, GRAY, (i, y), (i, y+h), 1)
    for j in range(y, y+h, tile_size):
        pygame.draw.line(surface, GRAY, (x, j), (x+w, j), 1)
    for i in range(x+5, x+w, tile_size*2):
        for j in range(y+5, y+h, tile_size*2):
            pygame.draw.rect(surface, LIGHT_GRAY, (i, j, 3, 3))

def draw_sofa_texture(surface, rect, color):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect)
    texture_color = safe_color(color, -10)
    for i in range(0, w+h, 6):
        pygame.draw.line(surface, texture_color, 
                       (x+i, y), (x, y+i), 1)
    seam_color = safe_color(color, -20)
    pygame.draw.rect(surface, seam_color, 
                   (x+2, y+2, w-4, h-4), 2)

# ---------------------- MySQL监控类 ----------------------
class MySQLMonitor:
    def __init__(self):
        self.conn = None
        self.slow_queries = []
        self.slow_count = 0

    def connect(self):
        try:
            self.conn = pymysql.connect(**MYSQL_CONFIG)
            return True
        except Exception as e:
            print(f"数据库连接失败：{e}")
            self.slow_queries = [{"sql_text": f"数据库连接失败: {e}", "query_time": 99.9}]
            self.slow_count = 1
            return False

    def get_slow_queries(self):
        if not self.conn:
            if not self.connect():
                return
        try:
            cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT sql_text, query_time, start_time
                FROM mysql.slow_log
                WHERE sql_text NOT LIKE '%mysql.slow_log%'
                ORDER BY start_time DESC
                LIMIT 20
            """)
            self.slow_queries = cursor.fetchall()
            self.slow_count = len(self.slow_queries)
            cursor.close()
        except Exception as e:
            print(f"查询慢日志失败：{e}")
            self.slow_queries = [{"sql_text": f"查询失败: {e}", "query_time": 99.9}]
            self.slow_count = 1

    def clear_slow_log(self):
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE mysql.slow_log")
            self.conn.commit()
            self.slow_queries = []
            self.slow_count = 0
            cursor.close()
        except Exception as e:
            print(f"清空慢日志失败：{e}")
            self.slow_queries = [{"sql_text": f"清空失败: {e}", "query_time": 99.9}]
            self.slow_count = 1

    def close(self):
        if self.conn:
            self.conn.close()

# ---------------------- 像素角色类（完全匹配图片形象） ----------------------
class PixelCharacter:
    def __init__(self):
        self.state = "normal"  # normal/angry
        self.size = 48        # 角色尺寸（适配图片大小）
        self.normal_pos = (680, 580)  # 正常位置（休闲区）
        self.angry_pos = (420, 450)   # 发怒位置（大屏前）
        self.x, self.y = self.normal_pos
        self.frame = 0
        self.animation_speed = 0.3
        self.animation_timer = 0

        # ---------------- 核心：匹配图片的角色像素帧 ----------------
        # 正常状态帧（灰色头发，平静表情）
        self.normal_frame = [
            # 48x48像素矩阵，1=填充，0=空白
            [0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0]
        ]

        # 发怒状态帧（红头发，愤怒表情）
        self.angry_frame = [
            [0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0]
        ]

    def update_state(self, slow_count):
        """更新角色状态和位置"""
        if slow_count > 0:
            self.state = "angry"
            self.x, self.y = self.angry_pos
        else:
            self.state = "normal"
            self.x, self.y = self.normal_pos

    def update_animation(self, dt):
        """更新动画帧（轻微晃动效果）"""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.frame = (self.frame + 1) % 2
            self.animation_timer = 0

    def draw(self):
        """绘制匹配图片的像素角色 + 状态切换"""
        # 选择当前帧和配色
        if self.state == "normal":
            current_frame = self.normal_frame
            hair_color = CHAR_HAIR_NORMAL
            face_color = CHAR_SKIN
            clothes_color = CHAR_CLOTHES
        else:
            current_frame = self.angry_frame
            hair_color = CHAR_HAIR_ANGRY  # 红头发
            face_color = CHAR_SKIN
            clothes_color = RED  # 发怒时衣服变红

        # 绘制48x48像素角色（严格匹配图片）
        scale = 1
        for i in range(48):
            for j in range(48):
                if current_frame[i][j] == 1:
                    pixel_x = self.x + j * scale
                    pixel_y = self.y + i * scale
                    # 区域划分（匹配图片的头部/身体）
                    if i < 12:  # 头发区域
                        draw_color = hair_color
                    elif i < 36:  # 脸部/身体区域
                        draw_color = face_color
                    else:  # 衣服区域
                        draw_color = clothes_color
                    # 绘制像素点
                    pygame.draw.rect(screen, draw_color, (pixel_x, pixel_y, scale, scale))
                    # 像素阴影（增加立体感）
                    shadow_color = safe_color(draw_color, -20)
                    if j % 6 == 0 and i % 6 == 0:
                        pygame.draw.rect(screen, shadow_color, 
                                       (pixel_x+1, pixel_y+1, scale-1, scale-1))

        # 绘制表情（核心区别：正常vs发怒）
        face_center_x = self.x + 24
        face_center_y = self.y + 20
        
        if self.state == "normal":
            # 正常表情：平静的眼睛 + 微笑
            # 左眼
            pygame.draw.circle(screen, CHAR_EYES, (face_center_x - 8, face_center_y - 4), 2)
            # 右眼
            pygame.draw.circle(screen, CHAR_EYES, (face_center_x + 8, face_center_y - 4), 2)
            # 微笑嘴巴
            pygame.draw.arc(screen, CHAR_MOUTH, (face_center_x - 8, face_center_y + 2, 16, 8), 0, 3.14, 1)
        else:
            # 发怒表情：怒目 + 咬牙
            # 怒目（斜线条）
            pygame.draw.line(screen, CHAR_EYES, (face_center_x - 10, face_center_y - 6), (face_center_x - 4, face_center_y - 2), 2)
            pygame.draw.line(screen, CHAR_EYES, (face_center_x + 4, face_center_y - 6), (face_center_x + 10, face_center_y - 2), 2)
            # 皱眉
            pygame.draw.line(screen, CHAR_EYES, (face_center_x - 12, face_center_y - 10), (face_center_x - 4, face_center_y - 6), 2)
            pygame.draw.line(screen, CHAR_EYES, (face_center_x + 4, face_center_y - 10), (face_center_x + 12, face_center_y - 6), 2)
            # 咬牙（直线嘴巴）
            pygame.draw.line(screen, CHAR_EYES, (face_center_x - 10, face_center_y + 6), (face_center_x + 10, face_center_y + 6), 3)
            # 愤怒腮红
            pygame.draw.circle(screen, (255, 182, 193), (face_center_x - 12, face_center_y + 2), 3)
            pygame.draw.circle(screen, (255, 182, 193), (face_center_x + 12, face_center_y + 2), 3)

# ---------------------- 办公室场景类 ----------------------
class OfficeScene:
    def __init__(self):
        self.areas = {
            "meeting_room": (100, 20, 300, 200),    # 会议室
            "office_area": (50, 220, 450, 400),     # 办公区
            "kitchen": (500, 220, 300, 150),        # 厨房区
            "relax_area": (500, 370, 300, 250),     # 休闲区
            "screen": (380, 380, 80, 60)            # 大屏位置
        }

    def draw_scene(self):
        """绘制精细化像素场景"""
        # 背景（深灰底色）
        screen.fill((20, 20, 30))

        # 1. 会议室（顶部）- 精细化木纹
        draw_wood_texture(screen, self.areas["meeting_room"], WOOD_MID)
        # 会议桌（深木纹）
        table_rect = (180, 50, 140, 100)
        draw_wood_texture(screen, table_rect, WOOD_DARK)
        # 椅子（带细节）
        chairs = [(170,60), (170,100), (170,140), (220,40),
                 (280,40), (330,60), (330,100), (330,140)]
        for (x,y) in chairs:
            pygame.draw.rect(screen, PLANT_GREEN, (x, y, 20, 20))
            pygame.draw.rect(surface=screen, color=safe_color(PLANT_GREEN, -10), rect=(x, y-5, 20, 5))
            pygame.draw.line(screen, WOOD_DARK, (x+2, y+20), (x+2, y+25), 1)
            pygame.draw.line(screen, WOOD_DARK, (x+18, y+20), (x+18, y+25), 1)
        # 会议室装饰（挂画）
        pygame.draw.rect(screen, WHITE, (230, 30, 40, 20))
        pygame.draw.rect(screen, GRAY, (235, 35, 30, 10))

        # 2. 办公区（左侧）- 木纹地板 + 精细化办公桌
        draw_wood_texture(screen, self.areas["office_area"], WOOD_LIGHT)
        # 办公桌（4张，带木纹）
        desks = [(80, 280), (280, 280), (80, 420), (280, 420)]
        for (x,y) in desks:
            desk_rect = (x, y, 120, 60)
            draw_wood_texture(screen, desk_rect, WOOD_DARK)
            for leg_x in [x+5, x+115]:
                for leg_y in [y+10, y+50]:
                    pygame.draw.rect(screen, WOOD_DARK, (leg_x, y+60, 5, 20))
            # 电脑（精细化）
            pygame.draw.rect(screen, GRAY, (x+10, y+10, 40, 30))
            pygame.draw.rect(screen, BLACK, (x+15, y+15, 30, 20))
            pygame.draw.rect(screen, LIGHT_GRAY, (x+15, y+45, 20, 5))
            pygame.draw.circle(screen, LIGHT_GRAY, (x+40, y+47), 2)
        # 办公区书架
        shelf_rects = [(60, 230, 80, 30), (180, 230, 80, 30), (300, 230, 80, 30)]
        for rect in shelf_rects:
            draw_wood_texture(screen, rect, WOOD_DARK)
            colors = [RED, GREEN, BLUE, WHITE, YELLOW]
            for i in range(8):
                pygame.draw.rect(screen, colors[i%5], (rect[0]+5+i*9, rect[1]+5, 7, 20))

        # 3. 厨房区（右上）- 瓷砖纹理
        draw_tile_texture(screen, self.areas["kitchen"], TILE_BEIGE)
        # 冰箱（精细化）
        pygame.draw.rect(screen, WHITE, (520, 250, 40, 80))
        pygame.draw.rect(screen, GRAY, (525, 255, 30, 70))
        pygame.draw.line(screen, BLACK, (525, 285), (555, 285), 1)
        # 咖啡机
        pygame.draw.rect(screen, GRAY, (600, 250, 30, 50))
        pygame.draw.circle(screen, BLACK, (615, 270), 3)
        # 微波炉
        pygame.draw.rect(screen, GRAY, (680, 250, 30, 30))
        pygame.draw.rect(screen, BLACK, (685, 255, 20, 20))

        # 4. 休闲区（右下）- 布料纹理
        draw_wood_texture(screen, (500, 370, 300, 50), WOOD_LIGHT)
        draw_tile_texture(screen, (500, 420, 300, 200), SCREEN_BLUE)
        # 沙发（布料纹理）
        sofa1_rect = (550, 400, 60, 80)
        sofa2_rect = (650, 400, 60, 80)
        draw_sofa_texture(screen, sofa1_rect, SOFA_PURPLE)
        draw_sofa_texture(screen, sofa2_rect, SOFA_PURPLE)
        # 沙发靠垫
        pygame.draw.rect(screen, SOFA_LIGHT, (560, 410, 20, 20))
        pygame.draw.rect(screen, SOFA_LIGHT, (660, 410, 20, 20))
        # 茶几（木纹）
        table_rect = (610, 430, 40, 20)
        draw_wood_texture(screen, table_rect, WOOD_DARK)
        # 茶几上的物品
        pygame.draw.circle(screen, COFFEE_CUP, (620, 440), 3)
        pygame.draw.rect(screen, WHITE, (630, 435, 5, 8))

        # 5. 监控大屏（精细化边框+网格）
        pygame.draw.rect(screen, GRAY, (self.areas["screen"][0]-5, self.areas["screen"][1]-5,
                                      self.areas["screen"][2]+10, self.areas["screen"][3]+10))
        pygame.draw.rect(screen, BLACK, self.areas["screen"])
        # 屏幕网格纹理
        for i in range(0, self.areas["screen"][2], 10):
            for j in range(0, self.areas["screen"][3], 10):
                pygame.draw.rect(screen, (0, 30, 60), 
                               (self.areas["screen"][0]+i, self.areas["screen"][1]+j, 9, 9))
        pygame.draw.rect(screen, WHITE, (self.areas["screen"][0]+2, self.areas["screen"][1]+2,
                                       self.areas["screen"][2]-4, self.areas["screen"][3]-4), 1)

        # 6. 绿植装饰（精细化）
        plants = [(120, 40), (300, 40), (70, 350), (700, 400), (700, 500)]
        for (x,y) in plants:
            pygame.draw.rect(screen, RED, (x, y, 8, 8))
            pygame.draw.circle(screen, PLANT_GREEN, (x+4, y-5), 3)
            pygame.draw.circle(screen, safe_color(PLANT_GREEN, -10), (x-2, y-2), 2)
            pygame.draw.circle(screen, safe_color(PLANT_GREEN, -10), (x+10, y-2), 2)

    def draw_screen_content(self, slow_queries):
        """绘制大屏内容"""
        screen_x, screen_y, screen_w, screen_h = self.areas["screen"]
        
        if not slow_queries:
            pygame.draw.rect(screen, SCREEN_BLUE, (screen_x+2, screen_y+2, screen_w-4, screen_h-4))
            for i in range(0, screen_w-4, 8):
                for j in range(0, screen_h-4, 8):
                    pygame.draw.rect(screen, safe_color(SCREEN_BLUE, +30), (screen_x+2+i, screen_y+2+j, 7, 7))
            text = mid_font.render("MySQL ✅", True, GREEN)
            text2 = small_font.render("无慢查询", True, WHITE)
            screen.blit(text, (screen_x + 15, screen_y + 15))
            screen.blit(text2, (screen_x + 20, screen_y + 35))
        else:
            slow = slow_queries[0]
            sql_content = slow.get("sql_text", "未知SQL语句")
            sql = sql_content[:20] + "..." if len(sql_content) > 20 else sql_content
            query_time_raw = slow.get("query_time", 0.0)
            query_time = timedelta_to_seconds(query_time_raw)
            time_text = f"耗时: {query_time:.2f}s"
            
            time_surf = small_font.render(time_text, True, WHITE)
            sql_surf = small_font.render(sql, True, YELLOW)
            screen.blit(time_surf, (screen_x + 6, screen_y + 6))
            screen.blit(sql_surf, (screen_x + 6, screen_y + 26))
            screen.blit(time_surf, (screen_x + 5, screen_y + 5))
            screen.blit(sql_surf, (screen_x + 5, screen_y + 25))

# ---------------------- 游戏主逻辑 ----------------------
def main():
    # 初始化组件
    monitor = MySQLMonitor()
    character = PixelCharacter()
    scene = OfficeScene()
    
    # 游戏状态
    running = True
    check_interval = 3
    last_check = time.time()
    dt = 0

    # 首次查询
    monitor.get_slow_queries()
    character.update_state(monitor.slow_count)

    # 提示信息
    info_text = mid_font.render("点击角色刷新 | R键手动刷新 | 空格键清空慢日志", True, WHITE)

    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if (character.x <= mx <= character.x + character.size and
                    character.y <= my <= character.y + character.size):
                    monitor.get_slow_queries()
                    character.update_state(monitor.slow_count)
            elif event.type == KEYDOWN:
                if event.key == K_r:
                    monitor.get_slow_queries()
                    character.update_state(monitor.slow_count)
                elif event.key == K_SPACE:
                    monitor.clear_slow_log()
                    character.update_state(0)

        # 定时检查
        if time.time() - last_check > check_interval:
            monitor.get_slow_queries()
            character.update_state(monitor.slow_count)
            last_check = time.time()

        # 更新动画
        character.update_animation(dt)

        # 绘制场景
        scene.draw_scene()
        scene.draw_screen_content(monitor.slow_queries)
        character.draw()
        
        # 绘制提示和统计
        screen.blit(info_text, (20, 650))
        stats_color = RED if monitor.slow_count>0 else GREEN
        stats = mid_font.render(f"慢查询数量: {monitor.slow_count}", True, stats_color)
        screen.blit(stats, (20, 620))

        # 更新屏幕
        pygame.display.flip()
        dt = clock.tick(60) / 1000

    # 清理资源
    monitor.close()
    pygame.quit()
    sys.exit()

# ---------------------- 启动游戏 ----------------------
if __name__ == "__main__":
    print("📌 安装依赖：pip install pygame pymysql")
    print("\n⚠️  修改MySQL连接信息（账号/密码）")
    print("🎮 操作说明：")
    print("  - 点击角色：手动刷新慢查询")
    print("  - R键：手动刷新慢查询")
    print("  - 空格键：清空慢日志（测试用）")
    input("\n按回车键开始游戏...")
    main()