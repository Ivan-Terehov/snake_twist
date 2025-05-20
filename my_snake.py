import pygame as pg
import pygame_menu
from abc import ABC, abstractmethod
import sys
import os
from random import choice, randint
from typing import Dict, Tuple, List, Set, Optional
import json
from datetime import datetime, timedelta


def resource_path(relative_path):
    """ Возвращает корректный путь для ресурсов """
    try:
        base_path = sys._MEIPASS  # Папка для ресурсов в EXE
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# region Константы
SCREEN_SIZE = (840, 480)
GRID_SIZE = 20
AREA_SIZE = (640, 480)
CENTER_POINT = (AREA_SIZE[0] // 2, AREA_SIZE[1] // 2)

COLORS = {
    'board': ('#97b2ad'),
    'snake': (225, 242, 29),
    'apple': (255, 0, 0),
    'gold': (255, 255, 0),
    'orange': (255, 150, 0),
    'plum': (150, 0, 255)
}

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

TURN_MAP = {
        pg.K_LEFT: LEFT,
        pg.K_RIGHT: RIGHT,
        pg.K_UP: UP,
        pg.K_DOWN: DOWN,
}

GRID_POSITIONS = {(x, y) for x in range(0, AREA_SIZE[0], GRID_SIZE)
                  for y in range(0, AREA_SIZE[1], GRID_SIZE)}

WALL_COLOR = (100, 100, 100)  # Цвет стен
WALL_POSITIONS = set()

# Рассчитать позиции стен (вертикальная и горизонтальная по центру, 2 клетки шириной)
vertical_wall_x = (AREA_SIZE[0] // 2) - GRID_SIZE  # Центр минус одна клетка
horizontal_wall_y = (AREA_SIZE[1] // 2) - GRID_SIZE  # Центр минус одна клетка

# Вертикальная стена (две клетки в ширину, полная высота)
for y in range(0, AREA_SIZE[1], GRID_SIZE):
    WALL_POSITIONS.add((vertical_wall_x, y))          # Левая колонка
    WALL_POSITIONS.add((vertical_wall_x + GRID_SIZE, y))  # Правая колонка

# Горизонтальная стена (две клетки в высоту, полная ширина)
for x in range(0, AREA_SIZE[0], GRID_SIZE):
    WALL_POSITIONS.add((x, horizontal_wall_y))          # Верхний ряд
    WALL_POSITIONS.add((x, horizontal_wall_y + GRID_SIZE))  # Нижний ряд

# Обновить DRAW_POSITIONS чтобы исключить стены
DRAW_POSITIONS = GRID_POSITIONS - WALL_POSITIONS

# region Инициализация Pygame
pg.init()
pg.mixer.init()
screen = pg.display.set_mode(SCREEN_SIZE)
clock = pg.time.Clock()
pg.display.set_caption('Изгиб питона')


images = {
    'fon': pg.image.load('fon.png'),
    'frame': pg.image.load('frame.png'),
    'logo': pg.image.load('logo2.png'),
    'logo_menu': pg.image.load('logo.png'),
    'wall': pg.image.load('wall.png'),
}

sounds = {
    'background_music': pg.mixer.Sound("background_music.mp3"),
    'ate': pg.mixer.Sound("ate.wav"),
}

class GameObject(ABC):
    """Абстрактный базовый класс для игровых объектов"""

    def __init__(self, position: Tuple[int, int], color: Tuple[int, int, int]):
        self.position = position
        self.color = color

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        """Отрисовка объекта на поверхности"""
        pass

    def draw_cell(self, surface: pg.Surface,
                  position: Tuple[int, int]) -> None:
        """Отрисовка одной клетки"""
        rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
        pg.draw.rect(surface, self.color, rect)


class Snake(GameObject):
    """Класс змейки"""

    def __init__(self):
        super().__init__(CENTER_POINT, COLORS['snake'])
        self.reset()

    def reset(self) -> None:
        """Сброс состояния змейки"""
        self.direction = RIGHT
        self.positions = [(0, 0)]
        self.length = 1

    def update_direction(self, new_dir: Tuple[int, int]) -> None:
        """Обновление направления движения"""
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (
        0, 0):
            self.direction = new_dir

    def move(self):
        x, y = self.get_head_position()
        dx, dy = self.direction
        new_x = x + dx * GRID_SIZE
        new_y = y + dy * GRID_SIZE

        # Обычная логика перемещения
        self.positions.insert(0, (new_x % AREA_SIZE[0], new_y % AREA_SIZE[1]))
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self, surface: pg.Surface) -> None:
        for pos in self.positions:
            self.draw_cell(surface, pos)

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]


class Wall(GameObject):  # Наследуем от GameObject
    def __init__(self):
        super().__init__((0, 0), WALL_COLOR)  # Позиция не важна, так как рисуем множество клеток
        self.positions = WALL_POSITIONS  # Используем глобальные позиции стен

    def draw(self, surface: pg.Surface) -> None:
        for pos in self.positions:
            self.draw_cell(surface, pos)


class Fruit(GameObject):
    """Базовый класс для фруктов"""

    def __init__(self, color: Tuple[int, int, int],
                 positions: Set[Tuple[int, int]]):
        super().__init__(self.randomize_position(positions), color)
        self.active = True

    @staticmethod
    def randomize_position(occupied: Set[Tuple[int, int]]) -> Tuple[
        int, int]:
        return choice(tuple(GRID_POSITIONS - set(occupied)))

    def respawn(self, occupied: Set[Tuple[int, int]]) -> None:
        self.position = self.randomize_position(occupied)
        self.active = True

    def draw(self, surface: pg.Surface) -> None:
        if self.active:
            self.draw_cell(surface, self.position)


class Apple(Fruit):
    """Обычное яблоко"""

    def __init__(self, snake_positions: List[Tuple[int, int]]):
        super().__init__(COLORS['apple'], set(snake_positions) | WALL_POSITIONS)


class Bonus(Fruit):
    """Бонусный фрукт с временным эффектом"""

    def __init__(self, color: Tuple[int, int, int], effect: str):
        super().__init__(color, set())
        self.effect = effect
        self.active = False
        self.spawn_time = None
        self.font = pg.font.Font(None, 24)  # Шрифт для отображения таймера

    def activate(self, occupied: Set[Tuple[int, int]]) -> None:
        self.respawn(occupied)
        self.spawn_time = datetime.now()

    def is_expired(self) -> bool:
        if self.spawn_time:
            return datetime.now() > self.spawn_time + timedelta(seconds=10)
        return True

    def draw(self, surface: pg.Surface) -> None:
        if self.active and not self.is_expired():
            # Отрисовываем базовую клетку
            super().draw(surface)

            # Рассчитываем оставшееся время
            elapsed = (datetime.now() - self.spawn_time).seconds
            remaining = max(0, 10 - elapsed)

            # Рендерим и позиционируем текст
            text = self.font.render(str(remaining), 1, (0, 0, 0))
            text_rect = text.get_rect(
                center=(
                    self.position[0] + GRID_SIZE // 2,
                    self.position[1] + GRID_SIZE // 2
                )
            )
            surface.blit(text, text_rect)


class GameState:
    def __init__(self, player_name: str):
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.font = pg.font.SysFont('comicsans', 27)
        self.snake = Snake()
        self.apple = Apple(self.snake.positions)
        self.bonuses = [
            Bonus(COLORS['orange'], 'length_decrease'),
            Bonus(COLORS['plum'], 'speed_decrease'),
            Bonus(COLORS['gold'], 'score_boost')
        ]
        self.speed = 0.1  # Используем FPS для управления скоростью
        self.score = 0
        self.best_score = 0
        self.paused = False
        self.player_name = player_name
        self.last_bonus_spawn = datetime.now()
        self.active_bonus = None
        self.best_score = self._load_best_score()  # Исправлено

    def _load_best_score(self) -> tuple[int, int]:
        scores = load_scores()
        return max(scores, key=lambda x: x['score'])['score'] if scores else 0


    def check_bonus_spawn(self):
        if datetime.now() - self.last_bonus_spawn > timedelta(seconds=15):
            available = [b for b in self.bonuses if not b.active]
            for bonus in available:
                conditions = {
                    'length_decrease': self.snake.length > 5,
                    'speed_decrease': self.speed > 1,
                    'score_boost': True
                }
                if conditions[bonus.effect]:
                    bonus.activate(set(self.snake.positions) | WALL_POSITIONS)
                    self.last_bonus_spawn = datetime.now()
                    self.active_bonus = bonus
                    break

    def handle_bonus_collision(self):
        head = self.snake.get_head_position()
        for bonus in self.bonuses:
            if bonus.active and bonus.position == head:
                if bonus.effect == 'length_decrease':
                    self.snake.length = max(3, self.snake.length - 1)
                    self.snake.positions = self.snake.positions[:self.snake.length]
                    self.score += 30
                elif bonus.effect == 'speed_decrease':
                    self.speed = max(1, self.speed - 1)
                    self.score += 30
                elif bonus.effect == 'score_boost':
                    time_active = (datetime.now() - bonus.spawn_time).seconds
                    points = max(0, 150 - 10 * time_active)
                    self.score += points
                    self.snake.length += 1
                    self.speed += 0.1
                bonus.active = False
                self.active_bonus = None
                sounds['ate'].play()

    def draw_all(self):
        """Отрисовывает все игровые объекты"""
        self.screen.fill(COLORS['board'])
        # Отрисовка
        screen.fill(COLORS['board'])
        screen.blit(images['fon'], (0, 0))
        screen.blit(images['frame'], (640, 0))
        screen.blit(images['logo'], (590, 0))

        # Отрисовка бонусов
        for bonus in self.bonuses:
            if bonus.active and not bonus.is_expired():
                bonus.draw(screen)

        # Отрисовка интерфейса
        interface_data = [
            f"Счёт: {self.score}",
            f"Рекорд: {self.best_score}",
            f"Скорость: {round(self.speed, 1)}",
            f"Игрок: {self.player_name}"
        ]

        for i, text in enumerate(interface_data):
            surf = self.font.render(text, 1, (0, 0, 0))
            screen.blit(surf, (655, 200 + i * 40))

        Wall().draw(screen)
        self.apple.draw(screen)
        self.snake.draw(screen)
        pg.display.update()


def save_score(name: str, score: int):
    try:
        with open('scores.json', 'r') as f:
            scores = json.load(f)
    except FileNotFoundError:
        scores = []

    scores.append({'name': name, 'score': score, 'date': str(datetime.now())})

    with open('scores.json', 'w') as f:
        json.dump(sorted(scores, key=lambda x: x['score'], reverse=True)[:10], f)


def load_scores():
    try:
        with open('scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)  # Возвращает словарь, а не список
    except FileNotFoundError:
        return {}

def handle_keys(snake: Snake, game_state) -> bool:
    """Обрабатывает клавиши и возвращает состояние паузы."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            raise SystemExit
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_p:
                return not game_state.paused  # Переключаем паузу
            elif event.key == pg.K_ESCAPE:
                pg.quit()
                raise SystemExit
            elif not game_state.paused and event.key in TURN_MAP:
                snake.update_direction(TURN_MAP[event.key])
    return game_state.paused


def create_menu_theme():
    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE
    theme.background_color = (215, 215, 215, 0)
    theme.widget_font_color = (0, 0, 0)
    theme.title_font_color = (0, 0, 0)
    theme.title_font_size = 30
    return theme

def update(screen, menu, image: str=None, coord: tuple[int, int]=None):
    screen.fill(COLORS['board'])
    if image:
        screen.blit(images[image], coord)
    menu.update(pg.event.get())
    menu.draw(screen)
    pg.display.update()


def name_input():
    screen = pg.display.set_mode((400, 200))
    menu = pygame_menu.Menu('Введите имя', 400, 200, theme=create_menu_theme())
    name_input = menu.add.text_input('Имя: ', default='Player 1')
    menu.add.button('Играть', lambda: main(name_input.get_value()))
    menu.add.button('Назад', game_menu)

    while True:
        update(screen, menu)

# Добавим функцию показа рекордов
def show_scores():
    screen = pg.display.set_mode((600, 400))
    menu = pygame_menu.Menu('Рекорды', 600, 400, theme=create_menu_theme())

    scores = load_scores()
    if not scores:
        menu.add.label('Пока нет рекордов!')
    else:
        for score in scores[:10]:
            menu.add.label(
                f"{score['name']}: {score['score']} ({score['date'][:10]})")

    menu.add.button('Назад', game_menu)

    while True:
        update(screen, menu)

def manual():
    """Инструкция"""
    screen = pg.display.set_mode((800, 600))
    menu = pygame_menu.Menu('Инструкция', 660, 600, theme=create_menu_theme())
    rules = [
        "Управление:",
        "← ↑ → ↓ - движение",
        "P - пауза",
        "ESC - выход",
        "",
        "Бонусы:",
        "🟡 Яблоко: +10 очков, +1 к длине",
        "🟡 Золотое: +50-150 очков, +1 к длине",
        "🟡 Апельсин: -1 к длине (каждые 30 сек)",
        "🟡 Слива: -0.5 скорости (шанс 15%)",
        "",
        "Бонусы исчезают через 10 секунд!"
    ]

    # Добавляем элементы
    for line in rules:
        menu.add.label(line, font_size=24)
    menu.add.button('Назад', game_menu)
    while True:
        update(screen, menu)


def game_menu():
    screen = pg.display.set_mode((250, 550))
    menu = pygame_menu.Menu('Меню', 200, 300, position=(25, 240, False),
                            theme=create_menu_theme())
    menu.add.button('Играть', name_input)
    menu.add.button('Рекорды', show_scores)
    menu.add.button('Правила', manual)
    menu.add.button('Выход', pygame_menu.events.EXIT)

    while True:
        update(screen, menu, 'logo_menu', (-70, -20))


def show_pause_menu(game_state) -> bool:
    """Отображает простое меню паузы с текстом"""
    # Создаем полупрозрачный оверлей
    overlay = pg.Surface(SCREEN_SIZE, pg.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Чёрный с 50% прозрачностью

    # Создаем шрифт для текста
    font = pg.font.Font(None, 30)
    text = font.render("Нажмите любую клавишу что бы продолжить", True,
                       (255, 255, 255))
    text_rect = text.get_rect(
        center=(AREA_SIZE[0] // 2, AREA_SIZE[1] // 2))

    # Отрисовываем текущее состояние игры
    game_state.draw_all()

    # Добавляем оверлей и текст
    game_state.screen.blit(overlay, (0, 0))
    game_state.screen.blit(text, text_rect)
    pg.display.update()

    # Ожидаем нажатия любой клавиши
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    raise SystemExit
                return False  # Возвращаемся в игру при любом нажатии


def main(player_name: str):
    """Основной игровой цикл"""
    state = GameState(player_name)
    sounds['background_music'].play(-1).set_volume(0.4)

    while True:
        state.paused = handle_keys(state.snake, state)

        if state.paused:
            # Убрали логику возврата в меню, теперь только продолжение игры
            show_pause_menu(state)
            state.paused = False
            continue

        state.check_bonus_spawn()
        state.snake.move()
        state.handle_bonus_collision()

        # Обновление скорости
        clock.tick(5 + state.speed)

        # Проверка столкновения с яблоком
        if state.snake.get_head_position() == state.apple.position:
            state.snake.length += 1
            state.score += 10
            state.speed += 0.1
            state.apple.respawn(set(state.snake.positions) | WALL_POSITIONS)
            sounds['ate'].play()

        # Проверка столкновения с телом
        if state.snake.get_head_position() in state.snake.positions[1:]:
            save_score(state.player_name, state.score)
            state.score = 0
            state.speed = 0.1
            state.snake.reset()

        # Проверка столкновения со стенами
        if state.snake.get_head_position() in WALL_POSITIONS:
            save_score(state.player_name, state.score)
            state.score = 0
            state.speed = 0.1
            state.snake.reset()

        state.draw_all()


if __name__ == '__main__':
    game_menu()

