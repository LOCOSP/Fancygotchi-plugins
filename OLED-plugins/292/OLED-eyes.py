import pwnagotchi.plugins as plugins
import os
import time
import logging
import subprocess
import threading
from PIL import Image, ImageDraw
from random import randint, uniform, choice
from pwnagotchi.ui.hw.libs.i2coled.oled import OLED

class VectorEyesAnimation(plugins.Plugin):
    __author__ = '@LOCOSP'
    __version__ = '1.0'
    __license__ = 'GPL3'
    __description__ = 'Animated Vector-like eyes on two OLED displays'

    def __init__(self):
        self.I2C1 = 0x3C
        self.I2C2 = 0x3D
        self.WIDTH = 128
        self.HEIGHT = 64
        self.active = True

        # Parametry oczu
        self.left_eye = {
            'width_default': 62,
            'height_default': 62,
            'width_current': 62,
            'height_current': 62,
            'width_next': 62,
            'height_next': 62,
            'radius': 6,
            'x': self.WIDTH//2,
            'y': self.HEIGHT//2,
            'x_next': self.WIDTH//2,
            'y_next': self.HEIGHT//2
        }
        
        self.right_eye = {
            'width_default': 62,
            'height_default': 62,
            'width_current': 62,
            'height_current': 62,
            'width_next': 62,
            'height_next': 62,
            'radius': 6,
            'x': self.WIDTH//2,
            'y': self.HEIGHT//2,
            'x_next': self.WIDTH//2,
            'y_next': self.HEIGHT//2
        }

        # Predefiniowane pozycje z natychmiastowym przeskokiem
        self.positions = {
            'N': {'pos': (self.WIDTH//2, 10),
                  'left': {'width': 45, 'height': 45},  # mniejsze przy patrzeniu w górę
                  'right': {'width': 45, 'height': 45}},
            'NE': {'pos': (self.WIDTH-30, 10),
                  'left': {'width': 45, 'height': 45},
                  'right': {'width': 50, 'height': 65}},
            'E': {'pos': (self.WIDTH-30, self.HEIGHT//2),
                  'left': {'width': 45, 'height': 50},
                  'right': {'width': 50, 'height': 70}},
            'SE': {'pos': (self.WIDTH-30, self.HEIGHT-10),
                  'left': {'width': 45, 'height': 45},
                  'right': {'width': 50, 'height': 65}},
            'S': {'pos': (self.WIDTH//2, self.HEIGHT-10),
                  'left': {'width': 45, 'height': 45},  # mniejsze przy patrzeniu w dół
                  'right': {'width': 45, 'height': 45}},
            'SW': {'pos': (30, self.HEIGHT-10),
                  'left': {'width': 50, 'height': 65},
                  'right': {'width': 45, 'height': 45}},
            'W': {'pos': (30, self.HEIGHT//2),
                  'left': {'width': 50, 'height': 70},
                  'right': {'width': 45, 'height': 50}},
            'NW': {'pos': (30, 10),
                  'left': {'width': 50, 'height': 65},
                  'right': {'width': 45, 'height': 45}},
            'C': {'pos': (self.WIDTH//2, self.HEIGHT//2),
                  'left': {'width': 62, 'height': 62},
                  'right': {'width': 62, 'height': 62}}
        }

        # Definicje nastrojów z bardziej wyraźnymi różnicami
        self.moods = {
            'normal': {
                'left': {'width': 62, 'height': 62},
                'right': {'width': 62, 'height': 62}
            },
            'happy_anime': {  # Nowy nastrój dla oczu w stylu anime > <
                'left': {'width': 45, 'height': 45, 'radius': 0, 'anime': True, 'direction': 'right'},  # >
                'right': {'width': 45, 'height': 45, 'radius': 0, 'anime': True, 'direction': 'left'}   # <
            },
            'tired': {
                'left': {'width': 62, 'height': 25},  # Bardziej zmęczone
                'right': {'width': 62, 'height': 25}
            },
            'angry': {
                'left': {'width': 70, 'height': 35, 'radius': 3},  # Bardziej ostre
                'right': {'width': 70, 'height': 35, 'radius': 3}
            },
            'happy': {
                'left': {'width': 65, 'height': 45},  # Bardziej wyraziste
                'right': {'width': 65, 'height': 45}
            },
            'confused': {
                'left': {'width': 50, 'height': 55},  # Większa asymetria
                'right': {'width': 70, 'height': 40}
            },
            'curious': {
                'left': {'width': 75, 'height': 75},  # Większe zaciekawienie
                'right': {'width': 75, 'height': 75}
            },
            'sleepy': {
                'left': {'width': 62, 'height': 15},  # Bardziej senne
                'right': {'width': 62, 'height': 15}
            }
        }

        # Parametry animacji
        self.is_blinking = False
        self.blink_progress = 0
        self.next_blink = time.time() + uniform(2, 5)
        self.current_position = 'C'
        self.current_mood = 'normal'
        self.next_mood_change = time.time() + uniform(5, 10)
        
        # Flagi dla animacji celownika
        self.is_targeting = False
        self.target_progress = 0
        self.target_frames = [
            {'outer': 70, 'inner': 40},  # Duże koło z małym w środku
            {'outer': 60, 'inner': 30},  # Zmniejszanie
            {'outer': 50, 'inner': 20},  # Jeszcze mniejsze
            {'outer': 40, 'inner': 10},  # Końcowe zmniejszenie
            {'outer': 30, 'inner': 5}    # Najmniejsze
        ]

        # Inicjalizacja wyświetlaczy
        self.init_displays()

    def init_displays(self):
        self.oled_left = OLED(address=self.I2C1, width=self.WIDTH, height=self.HEIGHT)
        self.oled_right = OLED(address=self.I2C2, width=self.WIDTH, height=self.HEIGHT)
        
        for display in [self.oled_left, self.oled_right]:
            display.Init()
            display.Clear()
            
        self.image_left = Image.new('1', (self.WIDTH, self.HEIGHT))
        self.image_right = Image.new('1', (self.WIDTH, self.HEIGHT))
        self.draw_left = ImageDraw.Draw(self.image_left)
        self.draw_right = ImageDraw.Draw(self.image_right)

    def set_mood(self, mood):
        """Ulepszona funkcja zmiany nastroju"""
        if mood in self.moods:
            logging.info(f"Vector Eyes: Setting mood to {mood}")
            self.current_mood = mood
            mood_data = self.moods[mood]
            
            # Natychmiastowa aktualizacja wymiarów oczu
            for eye, data in [('left', self.left_eye), ('right', self.right_eye)]:
                base_dims = mood_data[eye]
                data['width_current'] = base_dims['width']
                data['height_current'] = base_dims['height']
                if 'radius' in base_dims:
                    data['radius'] = base_dims['radius']
                else:
                    data['radius'] = 6  # Domyślny radius

    def look_at_position(self, position):
        """Natychmiastowa zmiana pozycji oczu z uwzględnieniem nastroju"""
        if position in self.positions:
            pos_data = self.positions[position]
            mood_data = self.moods[self.current_mood]
            x, y = pos_data['pos']
            
            # Natychmiastowa aktualizacja pozycji
            self.left_eye['x'] = x
            self.left_eye['y'] = y
            self.right_eye['x'] = x
            self.right_eye['y'] = y
            
            # Łączenie wymiarów pozycji i nastroju
            for eye, data in [('left', self.left_eye), ('right', self.right_eye)]:
                pos_dims = pos_data[eye]
                mood_dims = mood_data[eye]
                
                # Używamy wymiarów z pozycji, ale modyfikujemy je nastrojem
                data['width_current'] = min(pos_dims['width'], mood_dims['width'])
                data['height_current'] = min(pos_dims['height'], mood_dims['height'])
            
            self.current_position = position

    def blink(self):
        """Obsługa mrugania"""
        if time.time() >= self.next_blink:
            self.is_blinking = True
            self.blink_progress = 0
            self.next_blink = time.time() + uniform(2, 5)
        
        if self.is_blinking:
            self.blink_progress += 0.15
            if self.blink_progress >= 1:
                self.is_blinking = False
                self.blink_progress = 0

    def draw_target_eye(self, draw, x, y, outer_size, inner_size):
        """Rysowanie oka w trybie celownika - krzyżyk w kółku"""
        # Zewnętrzny okrąg (cienki)
        draw.ellipse(
            (x - outer_size//2, y - outer_size//2,
             x + outer_size//2, y + outer_size//2),
            outline=255,
            fill=0
        )
        
        # Pionowa linia krzyżyka
        draw.line(
            (x, y - inner_size//2, x, y + inner_size//2),
            fill=255,
            width=2
        )
        
        # Pozioma linia krzyżyka
        draw.line(
            (x - inner_size//2, y, x + inner_size//2, y),
            fill=255,
            width=2
        )

    def draw_anime_eye(self, draw, x, y, width, height, direction):
        """Ulepszone rysowanie oka w stylu anime (> lub <)"""
        if direction == 'right':  # Prawy ukos (>)
            # Główna linia ukośna
            draw.line(
                (x - width//2, y - height//2,  # Górny punkt
                 x + width//2, y),             # Środkowy punkt
                fill=255,
                width=3
            )
            draw.line(
                (x + width//2, y,              # Środkowy punkt
                 x - width//2, y + height//2),  # Dolny punkt
                fill=255,
                width=3
            )
        else:  # Lewy ukos (<)
            # Główna linia ukośna
            draw.line(
                (x + width//2, y - height//2,  # Górny punkt
                 x - width//2, y),             # Środkowy punkt
                fill=255,
                width=3
            )
            draw.line(
                (x - width//2, y,              # Środkowy punkt
                 x + width//2, y + height//2),  # Dolny punkt
                fill=255,
                width=3
            )

    def draw_eyes(self):
        """Rozszerzona funkcja rysowania oczu"""
        # Czyszczenie ekranów
        self.draw_left.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=0)
        self.draw_right.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=0)
        
        if self.is_targeting:
            # Rysowanie celowników
            frame = self.target_frames[min(int(self.target_progress), len(self.target_frames)-1)]
            self.draw_target_eye(self.draw_left, self.WIDTH//2, self.HEIGHT//2, 
                               frame['outer'], frame['inner'])
            self.draw_target_eye(self.draw_right, self.WIDTH//2, self.HEIGHT//2, 
                               frame['outer'], frame['inner'])
        else:
            # Sprawdzenie czy to tryb anime
            left_mood = self.moods[self.current_mood]['left']
            right_mood = self.moods[self.current_mood]['right']
            
            if 'anime' in left_mood and left_mood['anime']:
                # Rysowanie oczu w stylu anime
                self.draw_anime_eye(
                    self.draw_left,
                    self.left_eye['x'],
                    self.left_eye['y'],
                    self.left_eye['width_current'],
                    self.left_eye['height_current'],
                    left_mood['direction']
                )
                self.draw_anime_eye(
                    self.draw_right,
                    self.right_eye['x'],
                    self.right_eye['y'],
                    self.right_eye['width_current'],
                    self.right_eye['height_current'],
                    right_mood['direction']
                )
            else:
                # Standardowe rysowanie oczu
                left_height = self.left_eye['height_current']
                right_height = self.right_eye['height_current']
                if self.is_blinking:
                    left_height = max(4, left_height * (1 - self.blink_progress))
                    right_height = max(4, right_height * (1 - self.blink_progress))
                
                # Rysowanie lewego oka
                self.draw_left.rounded_rectangle(
                    (int(self.left_eye['x'] - self.left_eye['width_current']//2),
                     int(self.left_eye['y'] - left_height//2),
                     int(self.left_eye['x'] + self.left_eye['width_current']//2),
                     int(self.left_eye['y'] + left_height//2)),
                    radius=self.left_eye['radius'],
                    fill=255,
                    outline=255
                )
                
                # Rysowanie prawego oka
                self.draw_right.rounded_rectangle(
                    (int(self.right_eye['x'] - self.right_eye['width_current']//2),
                     int(self.right_eye['y'] - right_height//2),
                     int(self.right_eye['x'] + self.right_eye['width_current']//2),
                     int(self.right_eye['y'] + right_height//2)),
                    radius=self.right_eye['radius'],
                    fill=255,
                    outline=255
                )
        
        # Wyświetlanie
        self.oled_left.display(self.image_left)
        self.oled_right.display(self.image_right)

    def animate_eyes(self):
        """Zmodyfikowana główna pętla animacji z gwarantowanym czasem wykonania"""
        positions = [
            'C',            # Centrum
            'N', 'C',      # Góra
            'NE', 'C',     # Góra-prawo
            'E', 'C',      # Prawo
            'SE', 'C',     # Dół-prawo
            'S', 'C',      # Dół
            'SW', 'C',     # Dół-lewo
            'W', 'C',      # Lewo
            'NW', 'C'      # Góra-lewo
        ]
        position_index = 0
        last_position_change = time.time()
        last_blink = time.time()
        happy_counter = 0
        is_animating = False  # Flaga wskazująca czy trwa jakaś animacja
        
        while self.active:
            current_time = time.time()
            
            # Jeśli nie trwa żadna animacja
            if not is_animating:
                # Rozglądanie się
                if current_time - last_position_change > 3.5:  # Zwiększony odstęp czasowy
                    is_animating = True
                    position_index = (position_index + 1) % len(positions)
                    new_position = positions[position_index]
                    self.look_at_position(new_position)
                    
                    # Uśmiechnięte oczy tylko w centrum
                    if new_position == 'C':
                        happy_counter += 1
                        if happy_counter >= 4:
                            time.sleep(0.8)  # Dłuższa pauza przed uśmiechem
                            self.set_mood('happy_anime')
                            time.sleep(1.5)  # Dłuższy czas uśmiechu
                            self.set_mood('normal')
                            happy_counter = 0
                    
                    time.sleep(0.5)  # Pauza po zmianie pozycji
                    last_position_change = time.time()
                    is_animating = False
                
                # Mruganie tylko w pozycji centralnej
                elif self.current_position == 'C' and current_time - last_blink > uniform(3, 5):  # Dłuższy odstęp między mrugnięciami
                    is_animating = True
                    # Losowa liczba mrugnięć (1-3)
                    blink_count = randint(1, 3)
                    
                    for _ in range(blink_count):
                        # Pełny cykl mrugania
                        self.is_blinking = True
                        self.blink_progress = 0
                        
                        # Zapewnienie pełnego cyklu mrugania
                        while self.blink_progress < 1:
                            self.blink_progress += 0.15  # Wolniejsze mruganie
                            self.draw_eyes()
                            time.sleep(0.04)
                        
                        if _ < blink_count - 1:  # Jeśli to nie ostatnie mrugnięcie
                            time.sleep(0.2)  # Dłuższa pauza między mrugnięciami
                    
                    self.is_blinking = False
                    last_blink = time.time()
                    is_animating = False
            
            # Rysowanie
            self.draw_eyes()
            time.sleep(0.05)  # Wolniejsze odświeżanie

    def on_handshake(self, agent, filename, access_point, client_station):
        """Rozszerzona reakcja na handshake - animacja celownika z poprawnym powrotem"""
        logging.info("Vector Eyes: Handshake detected, displaying targeting animation")
        text = "Fuck yeaa! We got a handshake!"
        subprocess.run(["espeak", "-s", "110", "-p", "10", "-a", "150", text])
        
        # Zapisanie obecnego stanu
        original_mood = self.current_mood
        original_position = self.current_position
        
        # Zatrzymanie głównej animacji
        self.active = False
        time.sleep(0.1)
        
        # Włączenie trybu celownika
        self.is_targeting = True
        
        # Animacja celownika
        for _ in range(2):
            for i in range(20):
                self.target_progress = i / 4
                self.draw_eyes()
                time.sleep(0.02)
            for i in range(20, 0, -1):
                self.target_progress = i / 4
                self.draw_eyes()
                time.sleep(0.02)
        
        # Wyłączenie trybu celownika
        self.is_targeting = False
        self.target_progress = 0
        
        # Przywrócenie poprzedniego stanu
        self.current_mood = original_mood
        self.look_at_position(original_position)
        
        # Wznowienie głównej animacji w nowym wątku
        self.active = True
        self.animation_thread = threading.Thread(target=self.animate_eyes)
        self.animation_thread.start()
        
        # Wymuszenie jednego rysowania w poprzednim stanie
        self.draw_eyes()

    # Dodanie nowych reakcji na wydarzenia
    def on_sad(self, agent):
        """Reakcja na smutek"""
        self.set_mood('sad')
        time.sleep(2)
        self.set_mood('normal')

    def on_happy(self, agent):
        """Reakcja na szczęście - anime style"""
        self.set_mood('happy_anime')
        time.sleep(1.5)
        self.set_mood('normal')

    def on_excited(self, agent):
        """Zmodyfikowana reakcja na podekscytowanie"""
        self.set_mood('happy_anime')  # Najpierw anime oczy
        time.sleep(0.5)
        self.set_mood('curious')
        time.sleep(0.5)
        self.set_mood('happy_anime')  # Znowu anime oczy
        time.sleep(0.5)
        self.set_mood('normal')

    def on_bored(self, agent):
        """Reakcja na znudzenie"""
        self.set_mood('sleepy')
        time.sleep(2)
        self.set_mood('normal')

    def on_angry(self, agent):
        """Reakcja na złość"""
        self.set_mood('angry')
        time.sleep(1.5)
        self.set_mood('normal')

    def on_confused(self, agent):
        """Reakcja na dezorientację"""
        self.set_mood('confused')
        time.sleep(2)
        self.set_mood('normal')

    def on_sleep(self):
        """Reakcja na tryb uśpienia"""
        self.set_mood('sleepy')
        text = "I'll do power nap."
        subprocess.run(["espeak", "-s", "130", "-p", "20", "-a", "150", text])

    def on_wake(self):
        """Reakcja na wybudzenie"""
        self.set_mood('normal')

    def on_loaded(self):
        logging.info("Vector Eyes Animation plugin loaded")
        self.animation_thread = threading.Thread(target=self.animate_eyes)
        self.animation_thread.start()
        text = "Hi! My name is 3DRoiow... Lets hack the planet!"
        subprocess.run(["espeak", "-s", "130", "-p", "20", "-a", "150", text])

    def on_unload(self, ui):
        text = "No no no ! You terminating the only friend you have!"
        subprocess.run(["espeak", "-s", "130", "-p", "20", "-a", "150", text])
        self.active = False
        if hasattr(self, 'animation_thread'):
            self.animation_thread.join()
        
        for display, draw in [(self.oled_left, self.draw_left), 
                            (self.oled_right, self.draw_right)]:
            draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=0)
            display.display(draw._image)
        
        logging.info("Vector Eyes Animation plugin unloaded")
