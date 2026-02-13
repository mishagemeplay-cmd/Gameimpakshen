from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.core.window import Window
import webbrowser
from random import randint, random

Window.clearcolor = (0, 0, 0, 1)

# Глобальный прогресс
PLAYER_DATA = {
    "money": 0,
    "color": (0, 0.8, 1, 1),
    "heat_rate": 4,
    "high_score": 0
}

class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.layout = FloatLayout()
        self.layout.add_widget(Label(text="ULTRA SHOOTER", font_size='45sp', pos_hint={'center_x':0.5, 'center_y':0.88}, bold=True, color=(1, 0, 0.4, 1)))
        self.layout.add_widget(Label(text="Avtor: Grayp", font_size='20sp', pos_hint={'center_x':0.5, 'center_y':0.82}, color=(0.5,0.5,0.5,1)))
        
        tg_btn = Button(text="Разные игры в моем тгк", font_size='16sp', pos_hint={'center_x':0.5, 'center_y':0.78}, size_hint=(0.8, 0.05), background_color=(0,0,0,0), color=(0, 0.7, 1, 1))
        tg_btn.bind(on_press=lambda x: webbrowser.open("https://t.me/drivesueta"))
        self.layout.add_widget(tg_btn)
        
        self.info_lab = Label(text="", pos_hint={'center_x':0.5, 'center_y':0.65}, font_size='18sp')
        self.layout.add_widget(self.info_lab)

        self.layout.add_widget(Button(text="В БОЙ", size_hint=(0.7, 0.12), pos_hint={'center_x':0.5, 'center_y':0.45}, background_color=(1, 0, 0.3, 1), bold=True, on_press=self.go_game))
        self.layout.add_widget(Button(text="МАГАЗИН", size_hint=(0.7, 0.1), pos_hint={'center_x':0.5, 'center_y':0.3}, background_color=(0.2, 0.2, 0.2, 1), on_press=self.go_shop))
        self.add_widget(self.layout)

    def on_enter(self):
        self.info_lab.text = f"РЕКОРД: {PLAYER_DATA['high_score']} | КРИСТАЛЛЫ: {PLAYER_DATA['money']}"

    def go_game(self, inst): self.manager.current = 'game'
    def go_shop(self, inst): self.manager.current = 'shop'

class GameWidget(Widget):
    def __init__(self, ui_ref, **kw):
        super().__init__(**kw)
        self.ui = ui_ref
        self.player_size = 60
        self.init_game()
        Clock.schedule_interval(self.update, 1/60)
        Clock.schedule_interval(self.auto_fire, 0.12)

    def init_game(self):
        self.player_pos = [Window.width/2-30, 150]
        self.enemies, self.bullets, self.score, self.heat = [], [], 0, 0
        self.xp, self.level = 0, 1
        self.overheated = self.game_over = False
        self.bg_color = [0, 0, 0.1]

    def auto_fire(self, dt):
        if not self.game_over and not self.overheated:
            self.bullets.append([self.player_pos[0]+27, self.player_pos[1]+60])
            self.heat = min(100, self.heat + PLAYER_DATA['heat_rate'])
            if self.heat >= 100: self.overheated = True

    def update(self, dt):
        if self.game_over: return
        
        # Рекуперация энергии
        self.heat = max(0, self.heat - (1.2 if self.overheated else 0.5))
        if self.overheated and self.heat == 0: self.overheated = False
        
        # Движение пуль
        for b in self.bullets[:]:
            b[1] += 20
            if b[1] > Window.height: self.bullets.remove(b)

        # Жёсткий спавн
        spawn_rate = max(10, 40 - self.level * 2)
        if randint(1, spawn_rate) == 1:
            etype = 'norm'
            if self.level >= 2 and randint(1, 5) == 1: etype = 'kamikaze'
            if self.level >= 3 and randint(1, 10) == 1: etype = 'tank'
            
            size = 80 if etype == 'tank' else 50
            self.enemies.append({
                'pos': [randint(0, int(Window.width-size)), Window.height],
                'hp': 5 if etype == 'tank' else 1,
                'type': etype,
                'speed': randint(4, 7) + (self.level * 0.5)
            })

        # Обработка врагов
        for e in self.enemies[:]:
            if e['type'] == 'kamikaze':
                # Камикадзе летит к игроку по X
                if e['pos'][0] < self.player_pos[0]: e['pos'][0] += 3
                else: e['pos'][0] -= 3
                e['pos'][1] -= e['speed'] * 1.5
            else:
                e['pos'][1] -= e['speed']

            # Столкновение с пулей
            for b in self.bullets[:]:
                ex, ey = e['pos']
                size = 80 if e['type'] == 'tank' else 50
                if ex < b[0] < ex+size and ey < b[1] < ey+size:
                    if b in self.bullets: self.bullets.remove(b)
                    e['hp'] -= 1
                    if e['hp'] <= 0:
                        if e in self.enemies: self.enemies.remove(e)
                        self.score += 10 * self.level
                        self.xp += 20
                        PLAYER_DATA['money'] += 1
                        if self.xp >= 100: # Новый уровень
                            self.level += 1
                            self.xp = 0
                            self.enemies = [] # Supernova очистка
                        self.ui.text = f"LVL: {self.level} | SCORE: {self.score} | CRY: {PLAYER_DATA['money']}"
                    break
            
            # Смерть
            if (self.player_pos[0] < e['pos'][0]+40 and self.player_pos[0]+60 > e['pos'][0] and 
                self.player_pos[1] < e['pos'][1]+40 and self.player_pos[1]+60 > e['pos'][1]):
                self.die()
        
        self.enemies = [e for e in self.enemies if e['pos'][1] > -100]
        self.draw()

    def die(self):
        self.game_over = True
        if self.score > PLAYER_DATA['high_score']: PLAYER_DATA['high_score'] = self.score
        self.parent.add_widget(Button(text="СИСТЕМА СБОИТ\nВЕРНУТЬСЯ", size_hint=(0.6, 0.15), pos_hint={'center_x':0.5, 'center_y':0.5}, background_color=(1,0,0,1), on_press=lambda x: setattr(App.get_running_app().root, 'current', 'menu')))

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # Фон меняется от уровня
            Color(self.level*0.1, 0, 0.1, 1)
            Rectangle(pos=(0,0), size=Window.size)
            
            for b in self.bullets:
                Color(1, 1, 1); Rectangle(pos=(b[0], b[1]), size=(4, 20))
            
            # Игрок
            Color(*PLAYER_DATA['color'])
            Ellipse(pos=(self.player_pos[0], self.player_pos[1]), size=(60, 60))
            
            # Индикатор перегрева
            Color(1, 0, 0) if self.overheated else Color(0, 1, 0.8, 0.5)
            Line(circle=(self.player_pos[0]+30, self.player_pos[1]+30, 45, 0, self.heat*3.6), width=3)

            for e in self.enemies:
                if e['type'] == 'tank': Color(0.6, 0, 1)
                elif e['type'] == 'kamikaze': Color(1, 0.5, 0)
                else: Color(1, 0, 0.2)
                
                size = 80 if e['type'] == 'tank' else 50
                Rectangle(pos=(e['pos'][0], e['pos'][1]), size=(size, size))

    def on_touch_move(self, t):
        if not self.game_over: self.player_pos[0] = t.x - 30

class GameScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        f = FloatLayout()
        score_lab = Label(text=f"LVL: 1 | SCORE: 0 | CRY: {PLAYER_DATA['money']}", pos_hint={'center_x': 0.5, 'top': 0.98}, size_hint=(1, 0.1), bold=True, font_size='18sp')
        self.game = GameWidget(ui_ref=score_lab)
        f.add_widget(self.game); f.add_widget(score_lab)
        self.add_widget(f)

class ShopScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        l = FloatLayout()
        l.add_widget(Label(text="DARK MARKET", pos_hint={'y':0.4}, font_size='35sp', color=(1,0,0,1), bold=True))
        items = [("ЗОЛОТАЯ БРОНЯ (500)", 500, "skin", (1,0.8,0,1)), ("КРОВАВЫЙ НЕОН (1000)", 1000, "skin", (1,0,0.3,1)), ("МГНОВЕННЫЙ ОХЛАД (400)", 400, "up", 2.0)]
        y = 0.65
        for name, price, t, val in items:
            btn = Button(text=f"{name}", size_hint=(0.8, 0.08), pos_hint={'center_x':0.5, 'center_y':y}, background_color=(0.3,0.3,0.3,1))
            btn.bind(on_press=lambda x, p=price, tv=t, v=val: self.buy(p, tv, v))
            l.add_widget(btn); y -= 0.12
        l.add_widget(Button(text="ВЫХОД", size_hint=(0.5, 0.08), pos_hint={'center_x':0.5, 'center_y':0.1}, on_press=lambda x: setattr(self.manager, 'current', 'menu')))
        self.add_widget(l)

    def buy(self, p, t, v):
        if PLAYER_DATA['money'] >= p:
            PLAYER_DATA['money'] -= p
            if t == "skin": PLAYER_DATA['color'] = v
            else: PLAYER_DATA['heat_rate'] = v
            self.on_enter()

class CyberApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(ShopScreen(name='shop'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__': CyberApp().run()
