from abc import abstractmethod
from datetime import datetime, timedelta
import json
from random import choice
from typing import Dict, List, Optional, Set, Tuple


import pygame as pg
import pygame_menu


# Размеры различных окон.
SCREEN_SIZE = (860, 500)
SCREEN_NAME_INPUT = (400, 200)
SCREEN_SHOW_SCORES = (600, 400)
SCREEN_MANUAL = (800, 600)
SCREEN_GAME_MENU = (250, 550)

GRID_SIZE = 20
AREA_SIZE = (660, 500)

# Нужны лишь для тестов.
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT // GRID_SIZE)
CENTER_POINT = ((SCREEN_WIDTH // 2), (SCREEN_HEIGHT // 2))

BOARD_BACKGROUND_COLOR = ('#d9e0c1')
SNAKE_COLOR = ('#ffeb00')

# Константы для смены направления движения змейки.
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Угол поворота головы в зависимости от направления.
ANGLE = {
    UP: 180,
    DOWN: 0,
    LEFT: 270,
    RIGHT: 90
}

#
TURN_MAP = {
    pg.K_LEFT: LEFT,
    pg.K_RIGHT: RIGHT,
    pg.K_UP: UP,
    pg.K_DOWN: DOWN,
}

# Все доступные для игры ячейки.
GRID_POSITIONS = {(x, y) for x in range(0, AREA_SIZE[0], GRID_SIZE)
                  for y in range(0, AREA_SIZE[1], GRID_SIZE)}

WALL_POSITIONS = set()

# Позиции вертикальной стены.
for y in range(0, AREA_SIZE[1], GRID_SIZE):
    WALL_POSITIONS.add(((AREA_SIZE[0] // 2) - GRID_SIZE // 2, y))

# Позиции горизонтальной стены.
for x in range(0, AREA_SIZE[0], GRID_SIZE):
    WALL_POSITIONS.add((x, (AREA_SIZE[1] // 2) - GRID_SIZE // 2))

# Обновить DRAW_POSITIONS чтобы исключить стены
DRAW_POSITIONS = GRID_POSITIONS - WALL_POSITIONS

# Инициализация Pygame
pg.init()
pg.mixer.init()

# Основное игровое окно.
screen = pg.display.set_mode(SCREEN_SIZE)

clock = pg.time.Clock()
pg.display.set_caption('Изгиб питона')

# Загрузка изображений(pg.transform.scale - изменяет размер изображения).
images = {
    'fon': pg.image.load('assets/images/fon.png'),
    'frame': pg.image.load('assets/images/frame.png'),
    'logo': pg.transform.scale(pg.image.load('assets/images/logo.png'),
                               (300, 225)),
    'logo_menu': pg.image.load('assets/images/logo.png'),
    'manual': pg.transform.scale(pg.image.load('assets/images/manual.png'),
                                 (800, 600)),
    'snake_head': pg.transform.scale(
        pg.image.load('assets/images/snake_head.png'),
        (GRID_SIZE, GRID_SIZE)
    ),
    'snake_body': pg.transform.scale(
        pg.image.load('assets/images/snake_body.png'),
        (GRID_SIZE, GRID_SIZE)
    ),
    'apple': pg.transform.scale(pg.image.load('assets/images/apple.png'),
                                (GRID_SIZE, GRID_SIZE)),
    'cherry': pg.transform.scale(pg.image.load('assets/images/cherry.png'),
                                 (GRID_SIZE, GRID_SIZE)),
    'pulm': pg.transform.scale(pg.image.load('assets/images/pulm.png'),
                               (GRID_SIZE, GRID_SIZE)),
    'orange': pg.transform.scale(pg.image.load('assets/images/orange.png'),
                                 (GRID_SIZE, GRID_SIZE)),
}

# Загрузка звуков.
sounds = {
    'background_music': pg.mixer.Sound("assets/sounds/background_music.mp3"),
    'ate': pg.mixer.Sound("assets/sounds/ate.wav"),
}


class GameObject:
    """Базовый класс для игровых объектов."""

    def __init__(self, position: Tuple[int, int] = (0, 0),
                 body_color: Tuple[int, int, int] = None):
        self.position = position
        self.body_color = body_color

    @abstractmethod
    def draw(self) -> None:
        """Отрисовка объекта на поверхности"""
        pass

    def draw_images(self, image: pg.Surface,
                    position: Tuple[int, int]) -> None:
        """Отрисовка изображения объекта на заданной позиции."""
        screen.blit(image, position)


class Snake(GameObject):
    """
    Класс змейки.

    Attributes:
        direction (Tuple[int, int]): Текущее направление движения.
        positions (List[Tuple[int, int]]): Список позиций сегментов тела.
        length (int): Длина змейки.
    """

    def __init__(self, body_color: Tuple[int, int, int] = SNAKE_COLOR):
        super().__init__(body_color=body_color)
        self.reset()

    def reset(self) -> None:
        """Сброс состояния змейки в начальное положение."""
        self.direction = RIGHT
        self.positions = [(0, 0)]
        self.length = 1

    def update_direction(self, new_dir: Tuple[int, int]) -> None:
        """
        Обновление направления движения змейки.

        Args:
            new_dir: Новое направление движения (UP, DOWN, LEFT, RIGHT).
        """
        # Проверка на движение в противоположном направлении.
        if ((new_dir[0] + self.direction[0], new_dir[1] + self.direction[1])
                != (0, 0)):
            self.direction = new_dir

    def move(self) -> None:
        """Перемещение змейки в текущем направлении."""
        x, y = self.get_head_position()
        dx, dy = self.direction
        new_x = x + dx * GRID_SIZE
        new_y = y + dy * GRID_SIZE

        # Обновляет позиции с учётом границ игрового поля.
        self.positions.insert(0, (new_x % AREA_SIZE[0], new_y % AREA_SIZE[1]))
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self) -> None:
        """Отрисовка змейки на экране."""
        # Рисует тело.
        for pos in self.positions[1:]:
            self.draw_images(images['snake_body'], pos)

        # Рисует и поворачивает голову в зависимости от направления.
        rotated_head = pg.transform.rotate(images['snake_head'],
                                           ANGLE[self.direction])
        self.draw_images(rotated_head, self.get_head_position())

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]


class Fruit(GameObject):
    """
    Базовый класс для фруктов.

    Attributes:
        active (bool): Флаг активности фрукта (видим/невидим).
        image (pg.Surface): Изображение фрукта.
    """

    def __init__(self, positions: Set[Tuple[int, int]], image_name: str):
        """
        Инициализация фрукта.

        Args:
            positions: Множество занятых позиций.
            image_name: Ключ изображения в словаре images.
        """
        super().__init__(self.randomize_position(positions))
        self.active = True
        self.image = images[image_name]

    @staticmethod
    def randomize_position(occupied: Set[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Генерация случайной позиции для фрукта.

        Args:
            occupied: Множество занятых позиций.

        Returns:
            Случайная свободная позиция на игровом поле.
        """
        return choice(tuple(GRID_POSITIONS - set(occupied)))

    def respawn(self, occupied: Set[Tuple[int, int]]) -> None:
        """
        Перемещение фрукта на новую позицию.

        Args:
            occupied: Множество занятых позиций.
        """
        self.position = self.randomize_position(occupied)
        self.active = True

    def draw(self) -> None:
        """Отрисовка фрукта, если он активен."""
        if self.active:
            self.draw_images(self.image, self.position)


class Apple(Fruit):
    """Класс яблоко"""

    def __init__(self,
                 snake_positions: List[Tuple[int, int]] = [(0, 0)]):
        super().__init__(set(snake_positions) | WALL_POSITIONS, 'apple')


class Bonus(Fruit):
    """
    Бонусный фрукт с временным эффектом.

    Attributes:
        fruit_name (str): Название фрукта (для определения эффекта).
        spawn_time (datetime): Время появления бонуса.
        font (pg.font.Font): Шрифт для отображения таймера.
    """

    def __init__(self, fruit_name: str):
        # Определяем какое изображение использовать для бонуса
        # на основе эффекта
        super().__init__(set(), fruit_name)
        self.fruit_name = fruit_name
        self.active = False
        self.spawn_time = None
        self.font = pg.font.Font(None, 24)  # Шрифт для отображения таймера

    def activate(self, occupied: Set[Tuple[int, int]]) -> None:
        """
        Активация бонуса на игровом поле.

        Args:
            occupied: Множество занятых позиций.
        """
        self.respawn(occupied)
        self.spawn_time = datetime.now()

    def is_expired(self) -> bool:
        """
        Проверка истекшего времени жизни бонуса.

        Returns:
            True, если бонус истёк, иначе False.
        """
        if self.spawn_time:
            return datetime.now() > self.spawn_time + timedelta(seconds=10)
        return True

    def draw(self) -> None:
        """Отрисовка бонуса с таймером обратного отсчёта."""
        if self.active and not self.is_expired():
            # Отрисовывает базовое изображение фрукта.
            super().draw()

            # Рассчитывает оставшееся время.
            elapsed = (datetime.now() - self.spawn_time).seconds
            remaining = max(0, 10 - elapsed)

            # Создает и позиционируем текст с таймером.
            text = self.font.render(str(remaining), 1, (100, 0, 0))
            text_rect = text.get_rect(
                center=(
                    self.position[0] + GRID_SIZE // 2,
                    self.position[1] + GRID_SIZE // 2
                )
            )
            screen.blit(text, text_rect)


class GameState:
    """
    Класс для управления игровым состоянием.

    Attributes:
        screen (pg.Surface): Игровое окно.
        font (pg.font.Font): Шрифт для интерфейса.
        snake (Snake): Объект змейки.
        apple (Apple): Объект яблока.
        bonuses (List[Bonus]): Список бонусных фруктов.
        speed (float): Текущая скорость игры.
        score (int): Текущий счет игрока.
        best_score (int): Лучший счет из таблицы рекордов.
        paused (bool): Флаг паузы игры.
        player_name (str): Имя текущего игрока.
        last_bonus_spawn (datetime): Время последнего спавна бонуса.
        active_bonus (Optional[Bonus]): Активный бонусный фрукт.
    """

    def __init__(self, player_name: str):
        """
        Инициализация игрового состояния.

        Args:
            player_name: Имя текущего игрока.
        """
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.font = pg.font.SysFont('comicsans', 27)
        self.snake = Snake()
        self.apple = Apple(self.snake.positions)

        # Создаёт бонусные фрукты.
        self.bonuses = [
            Bonus('orange'),  # Уменьшение длины
            Bonus('pulm'),  # Уменьшение скорости
            Bonus('cherry')  # Бонус очков
        ]

        self.speed = 0.1
        self.score = 0
        self.best_score = 0
        self.paused = False
        self.player_name = player_name
        self.last_bonus_spawn = datetime.now()
        self.active_bonus = None
        self.best_score = self.load_best_score()

    def load_best_score(self) -> int:
        """
        Загрузка лучшего счета из таблицы рекордов.

        Returns:
            Лучший счет или 0, если таблица пуста.
        """
        scores = load_scores()
        return max(scores, key=lambda x: x['score'])['score'] if scores else 0

    def check_bonus_spawn(self):
        """Проверка условий и активация бонусных фруктов."""
        if datetime.now() - self.last_bonus_spawn > timedelta(seconds=15):
            # Ищет доступные для активации бонусы.
            available = [b for b in self.bonuses if not b.active]

            for bonus in available:
                # Условия для активации разных типов бонусов..
                conditions = {
                    'orange': self.snake.length > 5,  # Только если длина > 5.
                    'pulm': self.speed > 1,  # Только если скорость > 1.
                    'cherry': True  # Всегда доступна.
                }

                if conditions[bonus.fruit_name]:
                    # Активирует бонус на свободной позиции.
                    occupied = set(self.snake.positions) | WALL_POSITIONS
                    bonus.activate(occupied)
                    self.last_bonus_spawn = datetime.now()
                    self.active_bonus = bonus
                    break

    def handle_bonus_collision(self) -> None:
        """Обработка столкновений змейки с бонусными фруктами."""
        for bonus in self.bonuses:
            if (bonus.active and bonus.position
               == self.snake.get_head_position()):
                # Обработка разных типов бонусов.
                if bonus.fruit_name == 'orange':
                    # Уменьшает длину змейки (не менее 5 сегментов).
                    self.snake.length = max(5, self.snake.length - 1)
                    self.snake.positions \
                        = self.snake.positions[:self.snake.length]
                    self.score += 30

                elif bonus.fruit_name == 'pulm':
                    # Уменьшает скорость (не менее 1).
                    self.speed = max(1, self.speed - 1)
                    self.score += 30

                elif bonus.fruit_name == 'cherry':
                    # Бонус очков в зависимости от времени активации.
                    time_active = (datetime.now() - bonus.spawn_time).seconds
                    points = max(0, 150 - 10 * time_active)
                    self.score += points
                    self.snake.length += 1
                    self.speed += 0.1

                # Деактивирует бонус и проигрывает звук.
                bonus.active = False
                self.active_bonus = None
                sounds['ate'].play()

    def draw_all(self) -> None:
        """Отрисовка всех игровых объектов и статистики."""
        # Отрисовка изображений и фона.
        screen.fill(BOARD_BACKGROUND_COLOR)
        screen.blit(images['fon'], (0, 0))
        screen.blit(images['frame'], (660, 0))
        screen.blit(images['logo'], (610, 0))

        # Отрисовка бонусов
        for bonus in self.bonuses:
            if bonus.active and not bonus.is_expired():
                bonus.draw()

        # Отображение игровой статистики.
        interface_data = [
            f"Счёт: {self.score}",
            f"Рекорд: {self.best_score}",
            f"Скорость: {round(self.speed, 1)}",
            f"Игрок: {self.player_name}"
        ]
        # enumerate - формирует пару счётчик и элемент.
        for i, text in enumerate(interface_data):
            surf = self.font.render(text, 1, (0, 0, 0))
            screen.blit(surf, (675, 200 + i * 40))

        # Отрисовка яблока и змейки.
        self.apple.draw()
        self.snake.draw()

        pg.display.update()


def save_score(name: str, score: int) -> None:
    """
    Сохраняет результат игрока в файл рекордов.

    Args:
        name: Имя игрока.
        score: Достигнутый счет.
    """
    try:
        with open('scores.json', 'r') as f:
            scores = json.load(f)
    except FileNotFoundError:
        scores = []

    scores.append({
        'name': name,
        'score': score,
        'date': datetime.now().strftime('%Y-%m-%d')
    })

    with open('scores.json', 'w') as f:
        # Сохраняет только 5 лучших результатов.
        json.dump(sorted(scores,
                         key=lambda x: x['score'], reverse=True)[:5], f)


def load_scores() -> List[Dict]:
    """
    Загружает таблицу рекордов из файла.

    Returns:
        Список словарей с результатами игроков.
    """
    try:
        with open('scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def handle_keys(snake: Snake, game_state: GameState) -> bool:
    """
    Обрабатывает пользовательский ввод.

    Returns:
        Обновленное состояние паузы.
    """
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


def create_menu_theme(coord: Tuple[int, int]) -> pygame_menu.themes.Theme:
    """
    Создаёт тему для меню.

    Args:
        coord: Координаты для позиционирования заголовка.

    Returns:
        Объект темы меню.
    """
    theme = pygame_menu.themes.Theme(title_offset=coord)
    theme.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE
    theme.background_color = (215, 215, 215, 0)
    theme.widget_font_color = (0, 0, 0)
    theme.title_font_color = (0, 0, 0)
    theme.title_font_size = 30
    return theme


def update(screen: pg.Surface,
           menu: pygame_menu.Menu,
           image: pg.Surface = None,
           coord: Optional[Tuple[int, int]] = None) -> None:
    """
    Обновляет и отображает меню.

    Args:
        screen: Поверхность для отрисовки.
        menu: Объект меню.
        image: Изображения.
        coord: Координаты для отрисовки фонового изображения.
    """
    while True:
        screen.fill(BOARD_BACKGROUND_COLOR)
        if image:
            screen.blit(image, coord)
        menu.update(pg.event.get())
        menu.draw(screen)
        pg.display.update()


def name_input() -> None:
    """Окно ввода имени игрока."""
    screen = pg.display.set_mode(SCREEN_NAME_INPUT)
    menu = pygame_menu.Menu('Введите имя', 400, 200,
                            theme=create_menu_theme((100, 0)))
    name_input = menu.add.text_input('Имя: ', default='Player 1')
    menu.add.button('Играть', lambda: main(name_input.get_value()))
    menu.add.button('Назад', game_menu)
    update(screen, menu)


def show_scores() -> None:
    """Отображает таблицу рекордов."""
    screen = pg.display.set_mode(SCREEN_SHOW_SCORES)
    menu = pygame_menu.Menu('Рекорды', 600, 400,
                            theme=create_menu_theme((230, 0)))

    scores = load_scores()
    if not scores:
        menu.add.label('Пока нет рекордов!')
    else:
        for score in scores:
            menu.add.label(
                f"{score['name']}: {score['score']} ({score['date']})")

    menu.add.button('Назад', game_menu)

    update(screen, menu)


def manual() -> None:
    """Отображает инструкцию к игре."""
    screen = pg.display.set_mode(SCREEN_MANUAL)
    menu = pygame_menu.Menu('Инструкция', 660, 600,
                            theme=create_menu_theme((230, 0)))
    btn = menu.add.button('Назад', game_menu)
    btn.set_position(500, 500)

    update(screen, menu, images['manual'], coord=(0, 0))


def game_menu() -> None:
    """Главное меню игры."""
    screen = pg.display.set_mode(SCREEN_GAME_MENU)
    menu = pygame_menu.Menu('Меню', 200, 300, position=(25, 240, False),
                            theme=create_menu_theme((55, 0)))
    menu.add.button('Играть', name_input)
    menu.add.button('Рекорды', show_scores)
    menu.add.button('Правила', manual)
    menu.add.button('Выход', pygame_menu.events.EXIT)

    update(screen, menu, images['logo_menu'], (-70, -20))


def show_pause_menu(game_state) -> bool:
    """Отображает простое меню паузы с текстом."""
    # Полупрозрачный оверлей.
    overlay = pg.Surface(SCREEN_SIZE, pg.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Чёрный с 50% прозрачностью.

    # Создает текст.
    font = pg.font.Font(None, 30)
    text = font.render("Нажмите любую клавишу что бы продолжить", True,
                       (255, 255, 255))
    text_rect = text.get_rect(
        center=(AREA_SIZE[0] // 2, AREA_SIZE[1] // 2))

    # Отрисовывает текущее состояние игры.
    game_state.draw_all()

    # Добавляет оверлей и текст.
    game_state.screen.blit(overlay, (0, 0))
    game_state.screen.blit(text, text_rect)
    pg.display.update()

    # Ожидаем нажатия любой клавиши.
    # Пришлось реализовать отдельно из основной
    # функции управления это не работало.
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            # Возвращаемся в игру при любом нажатии.
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    raise SystemExit
                return False


def main(player_name: str = 'Player 1') -> None:
    """
    Основной игровой цикл.

    Args:
        player_name: Имя текущего игрока.
    """
    state = GameState(player_name)
    sounds['background_music'].play(-1).set_volume(0.4)

    while True:
        state.paused = handle_keys(state.snake, state)

        # Обработка паузы.
        if state.paused:
            show_pause_menu(state)
            state.paused = False
            continue

        # Логика игрового процесса.
        state.check_bonus_spawn()
        state.snake.move()
        state.handle_bonus_collision()

        # Обновление скорости.
        clock.tick(5 + state.speed)

        # Проверка столкновения с яблоком
        if state.snake.get_head_position() == state.apple.position:
            state.snake.length += 1
            state.score += 10
            state.speed += 0.1
            state.apple.respawn(set(state.snake.positions) | WALL_POSITIONS)
            sounds['ate'].play()

        # Проверка столкновения с телом.
        if state.snake.get_head_position() in state.snake.positions[1:]:
            save_score(state.player_name, state.score)
            state.score = 0
            state.speed = 0.1
            state.snake.reset()

        # Проверка столкновения со стенами.
        if state.snake.get_head_position() in WALL_POSITIONS:
            save_score(state.player_name, state.score)
            state.score = 0
            state.speed = 0.1
            state.snake.reset()

        # Отрисовка игрового состояния.
        state.draw_all()


if __name__ == '__main__':
    game_menu()
