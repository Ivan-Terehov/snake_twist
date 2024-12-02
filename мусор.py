import pygame
import pygame_menu
import sys
from random import choice

from pygame import K_ESCAPE

SCREEN_WIDTH, SCREEN_HEIGHT = 840, 480
GRID_SIZE = 20
AREA_WIDTH = (0, 640)
AREA_HEIGHT = (0, 480)
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT // GRID_SIZE)
CENTER_POINT = ((AREA_WIDTH[1] // 2), (AREA_HEIGHT[1] // 2))

# Цвет фона - черный. Я её не использую, но без неё тесты не проходят.
BOARD_BACKGROUND_COLOR = (170, 215, 81)

# Цвет границы ячейки.
BORDER_COLOR = (162, 209, 73)

# Цвет ячейки
BOX_COLOR = (7, 148, 33)

# Цвет змейки.
SNAKE_COLOR = (225, 242, 29)

# Цвет яблока.
APPLE_COLOR = (255, 0, 0)

# Цвет золотого яблока.
GOLD_APPLE = (255, 215, 0)

# Цвет апельсина.
ORANGE = (255, 150, 0)

# Цвет сливы.
PULM = (150, 0, 255)


# Направления движения.
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Настройка игрового окна.
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
draw_position = [(x, y) for x in range(AREA_WIDTH[0], AREA_WIDTH[1], 20)
                        for y in range(AREA_HEIGHT[0], AREA_HEIGHT[1], 20)]
# Настройка времени.
clock = pygame.time.Clock()
images = {'fon' : pygame.image.load('fon.png.'),
'frame' : pygame.image.load('frame.png.'),
'logo' : pygame.image.load('logo.png.'),
'logo_menu' : pygame.image.load('logo_2.png.'),
'wall_level_2' : pygame.image.load('wall_level_3.png.')}


def handle_keys(game_object):
    """Обрабатывает нажатие клавиш"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            if ((event.key == pygame.K_UP or event.key == pygame.K_w)
                    and game_object.direction != DOWN):
                game_object.next_direction = UP
            elif ((event.key == pygame.K_DOWN or event.key == pygame.K_s)
                  and game_object.direction != UP):
                game_object.next_direction = DOWN
            elif ((event.key == pygame.K_LEFT or event.key == pygame.K_a)
                  and game_object.direction != RIGHT):
                game_object.next_direction = LEFT
            elif ((event.key == pygame.K_RIGHT or event.key == pygame.K_d)
                  and game_object.direction != LEFT):
                game_object.next_direction = RIGHT
            elif event.key == K_ESCAPE:
                # ESC key pressed
                pygame.quit()
                sys.exit()


class GameObject:
    """Общее описание объектов игры."""

    def __init__(self, position=CENTER_POINT, bady_color=None) -> None:
        """Инициализирует базовые атрибуты объекта."""
        self.position = position
        self.body_color = bady_color

    def randomize_position(self):
        """Устанавливает случайное положение яблока."""
        x1, x2 = AREA_WIDTH
        y1, y2 = AREA_HEIGHT
        self.position = choice(draw_position)

    def draw_cell(self, position):
        """Отрисовка клетки."""
        cell = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, cell)

    def draw(self):
        """Метод для переопределения в дочерних классах"""
        pass

class Snake(GameObject):
    """Описание змейки"""

    def __init__(self):
        """Инициализирует начальное состояние змейки."""
        super().__init__(position=CENTER_POINT, bady_color=SNAKE_COLOR)
        self.length = 1
        self.speed = 1
        self.positions = [(0, 0)]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None

    def update_direction(self):
        """Обновляет направление движения змейки."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def move(self):
        """Обновляет позицию змейки."""
        self.update_direction()
        # Записываем последнюю позицию змейки для последующего затирания.
        self.last = self.positions[-1]
        # Обновляем координаты головы. % позволяет перемещаться сквозь стены.
        new_positions = ((self.get_head_position()[0] + self.direction[0]
                          * GRID_SIZE) % AREA_WIDTH[1],
                         (self.get_head_position()[1] + self.direction[1]
                          * GRID_SIZE) % AREA_HEIGHT[1])
        # Обработка столкновения со своим телом.
        if new_positions in self.positions:
            self.reset()
        else:
            self.positions.insert(0, new_positions)
            # Затирание хвоста следа.
            if len(self.positions) > self.length:
                self.positions.pop()
        self.draw()

    def move_leve_2(self):
        """Обновляет позицию змейки."""
        self.update_direction()
        # Записываем последнюю позицию змейки для последующего затирания.
        self.last = self.positions[-1]
        # Обновляем координаты головы. % позволяет перемещаться сквозь стены.
        new_positions = ((self.get_head_position()[0] + self.direction[0]
                          * GRID_SIZE) % AREA_WIDTH[1],
                         (self.get_head_position()[1] + self.direction[1]
                          * GRID_SIZE) % AREA_HEIGHT[1])
        x, y = new_positions
        # Обработка столкновения со своим телом.
        if new_positions in self.positions or (x == 320 or y == 240 or x == 300 or y == 220):
            self.reset()
        else:
            self.positions.insert(0, new_positions)
            # Затирание хвоста следа.
            if len(self.positions) > self.length:
                self.positions.pop()
            self.draw()

    def draw(self):
        """Отрисовывает змейку на экране, затирая след"""
        for position in self.positions:
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, self.body_color, rect)

        # Отрисовка головы змейки.
        self.draw_cell(self.positions[0])

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]

    def reset(self):
        """Сбрасывает змейку в начальное состояние"""
        self.length = 1
        self.positions = [(0, 0)]
        # Очищает игровое поле после столкновения.

    def snake_speed(self):
        """Позволяет изменять скорость змейки с набором очков"""
        self.speed = self.length // 5

class Apple(GameObject):
    """Описание яблока"""

    def __init__(self):
        """Задаёт цвет и позицию яблока."""
        super().__init__(bady_color=APPLE_COLOR)
        self.randomize_position()

    def draw(self):
        """Отрисовывает объекта на игровом поле."""
        self.draw_cell(self.position)

class Apple(GameObject):
    """Описание яблока"""

    def __init__(self):
        """Задаёт цвет и позицию яблока."""
        super().__init__(bady_color=APPLE_COLOR)
        self.randomize_position()

    def draw(self):
        """Отрисовывает объекта на игровом поле."""
        self.draw_cell(self.position)

class Gold(GameObject):
    """Описание апельсина(бонус к очкам)"""

    def __init__(self, body_color=GOLD_APPLE):
        """Задаёт цвет и позицию яблока."""
        super().__init__()
        self.randomize_position()
        self.body_color = body_color

    def draw(self):
        """Отрисовывает объекта на игровом поле."""
        self.draw_cell(self.position)

class Orange(GameObject):
    """Описание сливы(уменьшение длины)"""

class Plum(GameObject):
    """Описание сливы(уменьшение скорости)"""

def main():
    """Запуск игры"""
    # Создание поверхности для игры.
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption('Изгиб питона')
    apple = Apple()
    snake = Snake()
    font = pygame.font.SysFont('comicsans', 27)
    global AREA_WIDTH
    global AREA_HEIGHT
    AREA_WIDTH = (20, 620)
    AREA_HEIGHT = (20, 460)

    while True:
        snake.snake_speed()
        # Настройка скорости змейки.
        clock.tick(5 + snake.speed)
        # Активация управления.
        handle_keys(snake)
        screen.fill(BOARD_BACKGROUND_COLOR)
        screen.blit(images['fon'], (0, 0))
        screen.blit(images['wall_level_2'], (0, 0))
        screen.blit(images['frame'], (640, 0))
        screen.blit(images['logo'], (655, 20))
        apple.draw()
        snake.move_leve_2()
        # Обработка события поедания яблока.
        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position()
        score_font = font.render(f"Cчёт: {(snake.length - 1) * 10}", 1,
                                 (250, 160, 70))
        speed_font = font.render(f"Скорость: {snake.speed}", 1, (250, 160, 70))
        screen.blit(score_font, (655, 160))
        screen.blit(speed_font, (655, 200))
        pygame.display.update()

def main_menu():
    """Главное меню игры"""
    # Создает поверхность для меню.
    screen = pygame.display.set_mode((250, 480), 0, 32)
    pygame.display.set_caption('Изгиб питона')
    pygame.init()
    while True:
        # Копирует готовую тему.
        mytheme = pygame_menu.themes.THEME_DARK.copy()
        # Изменяет стиль шрифта для кнопок.
        mytheme.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
        # Изменяет стиль шрифта для заголовка.
        mytheme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
        # Изменяем стиль заголовка.
        mytheme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE
        # Изменяет цвет фона в меню (последний аргумент прозрачность).
        mytheme.background_color = (215,215, 215, 0),
        # Изменяет цвет меню.
        mytheme.widget_font_color = (0, 0, 0),
        # Изменяет цвет заголовка.
        mytheme.title_font_color= (0, 0, 0)
        # Изменяет размер заголовка.
        mytheme.title_font_size = 30
        # Создание окна и виджета меню.
        menu = pygame_menu.Menu('Меню',200, 200,
                                position=(25, 240, False),
                                theme=mytheme)
        menu.add.button('Играть', main)
        menu.add.button('Выход', pygame_menu.events.EXIT)
        while True:
            screen.fill(BOARD_BACKGROUND_COLOR)
            screen.blit(images['logo_menu'], (0, 0))
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    exit()
            if menu.is_enabled():
                menu.draw(screen)
                menu.update(events)

            pygame.display.update()

if __name__ == '__main__':
    main_menu()