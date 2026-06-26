"""A keyboard-controlled Tetris game with a bright voxel-inspired look.

Run with:
    python main.py

Controls:
    Left/Right or A/D  - move
    Down or S          - soft drop
    Up or W/X          - rotate
    Space              - hard drop
    P                  - pause/resume
    R                  - restart after game over
"""

from __future__ import annotations

import random
import tkinter as tk
from dataclasses import dataclass
from typing import Iterable

CELL_SIZE = 32
COLUMNS = 10
ROWS = 20
SIDEBAR = 210
BOARD_PADDING = 18
WINDOW_WIDTH = COLUMNS * CELL_SIZE + SIDEBAR + BOARD_PADDING * 3
WINDOW_HEIGHT = ROWS * CELL_SIZE + BOARD_PADDING * 2
TICK_MS = 16

# Tetromino matrices use 1s for filled cells. Rotations are generated at runtime.
SHAPES: dict[str, list[list[int]]] = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

# Saturated, toy-like colors to evoke the friendly blocky Crossy Road mood.
COLORS = {
    "I": "#47D9FF",
    "O": "#FFD84A",
    "T": "#B980FF",
    "S": "#64E65A",
    "Z": "#FF6D6D",
    "J": "#5C8CFF",
    "L": "#FFA24A",
}

BG_COLOR = "#8CE35C"
BOARD_COLOR = "#EAF8FF"
GRID_COLOR = "#C8E9F2"
TEXT_COLOR = "#27524A"
SHADOW_COLOR = "#000000"


@dataclass
class Piece:
    kind: str
    matrix: list[list[int]]
    row: int = 0
    col: int = 3

    @property
    def color(self) -> str:
        return COLORS[self.kind]

    def cells(self, matrix: list[list[int]] | None = None, row: int | None = None, col: int | None = None) -> Iterable[tuple[int, int]]:
        shape = matrix if matrix is not None else self.matrix
        base_row = self.row if row is None else row
        base_col = self.col if col is None else col
        for r, line in enumerate(shape):
            for c, value in enumerate(line):
                if value:
                    yield base_row + r, base_col + c


class TetrisGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Voxel Tetris")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.root.bind("<KeyPress>", self.on_key_press)

        self.board_x = BOARD_PADDING
        self.board_y = BOARD_PADDING
        self.sidebar_x = self.board_x + COLUMNS * CELL_SIZE + BOARD_PADDING
        self.drop_timer = 0
        self.running = True
        self.paused = False
        self.reset()
        self.loop()

    def reset(self) -> None:
        self.grid: list[list[str | None]] = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.bag: list[str] = []
        self.current = self.new_piece()
        self.next_piece = self.new_piece()
        self.drop_interval = 650
        self.drop_timer = 0
        self.paused = False

    def refill_bag(self) -> None:
        self.bag = list(SHAPES)
        random.shuffle(self.bag)

    def new_piece(self) -> Piece:
        if not self.bag:
            self.refill_bag()
        kind = self.bag.pop()
        matrix = [row[:] for row in SHAPES[kind]]
        return Piece(kind=kind, matrix=matrix, row=0, col=(COLUMNS - len(matrix[0])) // 2)

    def loop(self) -> None:
        if self.running:
            if not self.paused and not self.game_over:
                self.drop_timer += TICK_MS
                if self.drop_timer >= self.drop_interval:
                    self.drop_timer = 0
                    self.soft_drop()
            self.draw()
            self.root.after(TICK_MS, self.loop)

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key == "p" and not self.game_over:
            self.paused = not self.paused
            return
        if key == "r" and self.game_over:
            self.reset()
            return
        if self.paused or self.game_over:
            return

        if key in {"left", "a"}:
            self.move(0, -1)
        elif key in {"right", "d"}:
            self.move(0, 1)
        elif key in {"down", "s"}:
            self.soft_drop(add_score=True)
        elif key in {"up", "w", "x"}:
            self.rotate()
        elif key == "space":
            self.hard_drop()

    def valid_position(
        self,
        piece: Piece,
        row: int | None = None,
        col: int | None = None,
        matrix: list[list[int]] | None = None,
    ) -> bool:
        for r, c in piece.cells(matrix=matrix, row=row, col=col):
            if c < 0 or c >= COLUMNS or r >= ROWS:
                return False
            if r >= 0 and self.grid[r][c] is not None:
                return False
        return True

    def move(self, row_delta: int, col_delta: int) -> bool:
        new_row = self.current.row + row_delta
        new_col = self.current.col + col_delta
        if self.valid_position(self.current, row=new_row, col=new_col):
            self.current.row = new_row
            self.current.col = new_col
            return True
        return False

    def soft_drop(self, add_score: bool = False) -> None:
        if self.move(1, 0):
            if add_score:
                self.score += 1
        else:
            self.lock_piece()

    def hard_drop(self) -> None:
        distance = 0
        while self.move(1, 0):
            distance += 1
        self.score += distance * 2
        self.lock_piece()

    def rotate(self) -> None:
        if self.current.kind == "O":
            return
        rotated = [list(row) for row in zip(*self.current.matrix[::-1])]
        # Small wall-kick offsets keep rotation pleasant near edges.
        for offset in (0, -1, 1, -2, 2):
            if self.valid_position(self.current, col=self.current.col + offset, matrix=rotated):
                self.current.matrix = rotated
                self.current.col += offset
                return

    def lock_piece(self) -> None:
        for r, c in self.current.cells():
            if r < 0:
                self.game_over = True
                return
            self.grid[r][c] = self.current.color
        self.clear_lines()
        self.current = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_position(self.current):
            self.game_over = True

    def clear_lines(self) -> None:
        kept_rows = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = ROWS - len(kept_rows)
        if cleared:
            self.grid = [[None for _ in range(COLUMNS)] for _ in range(cleared)] + kept_rows
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.drop_interval = max(110, 650 - (self.level - 1) * 55)
            self.score += {1: 100, 2: 300, 3: 500, 4: 800}[cleared] * self.level

    def ghost_row(self) -> int:
        row = self.current.row
        while self.valid_position(self.current, row=row + 1):
            row += 1
        return row

    def draw(self) -> None:
        self.canvas.delete("all")
        self.draw_background()
        self.draw_board()
        self.draw_sidebar()
        if self.paused:
            self.draw_overlay("PAUSE", "Press P to continue")
        if self.game_over:
            self.draw_overlay("GAME OVER", "Press R to restart")

    def draw_background(self) -> None:
        # Simple chunky grass tiles and road-like stripes for a playful voxel scene.
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            color = "#94EA65" if (y // CELL_SIZE) % 2 == 0 else "#82D954"
            self.canvas.create_rectangle(0, y, WINDOW_WIDTH, y + CELL_SIZE, fill=color, outline="")
        for x in range(18, WINDOW_WIDTH, 96):
            self.canvas.create_rectangle(x, 26, x + 28, 46, fill="#B7F17A", outline="")
            self.canvas.create_rectangle(x + 8, WINDOW_HEIGHT - 64, x + 34, WINDOW_HEIGHT - 42, fill="#6FCB4D", outline="")

    def draw_board(self) -> None:
        x0 = self.board_x
        y0 = self.board_y
        x1 = x0 + COLUMNS * CELL_SIZE
        y1 = y0 + ROWS * CELL_SIZE
        self.canvas.create_rectangle(x0 + 8, y0 + 10, x1 + 8, y1 + 10, fill="#5DA444", outline="")
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=BOARD_COLOR, outline="#FFFFFF", width=4)

        for row in range(ROWS):
            for col in range(COLUMNS):
                x = x0 + col * CELL_SIZE
                y = y0 + row * CELL_SIZE
                self.canvas.create_rectangle(x, y, x + CELL_SIZE, y + CELL_SIZE, outline=GRID_COLOR)
                color = self.grid[row][col]
                if color:
                    self.draw_voxel_cell(x, y, color)

        ghost_color = self.current.color
        for r, c in self.current.cells(row=self.ghost_row()):
            if r >= 0:
                self.draw_voxel_cell(x0 + c * CELL_SIZE, y0 + r * CELL_SIZE, ghost_color, ghost=True)
        for r, c in self.current.cells():
            if r >= 0:
                self.draw_voxel_cell(x0 + c * CELL_SIZE, y0 + r * CELL_SIZE, self.current.color)

    def draw_sidebar(self) -> None:
        x = self.sidebar_x
        self.canvas.create_rectangle(x, BOARD_PADDING, WINDOW_WIDTH - BOARD_PADDING, WINDOW_HEIGHT - BOARD_PADDING, fill="#F6FFE8", outline="#FFFFFF", width=4)
        self.draw_text(x + 18, 48, "VOXEL\nTETRIS", 24, anchor="nw")
        self.draw_text(x + 18, 145, f"Score\n{self.score}", 16, anchor="nw")
        self.draw_text(x + 18, 225, f"Lines\n{self.lines}", 16, anchor="nw")
        self.draw_text(x + 18, 305, f"Level\n{self.level}", 16, anchor="nw")
        self.draw_text(x + 18, 392, "Next", 16, anchor="nw")
        self.draw_preview(x + 60, 445)
        controls = "←/→ A/D: move\n↓ S: soft drop\n↑ W X: rotate\nSpace: hard drop\nP: pause"
        self.draw_text(x + 18, 555, controls, 11, anchor="nw")

    def draw_preview(self, x: int, y: int) -> None:
        for r, row in enumerate(self.next_piece.matrix):
            for c, value in enumerate(row):
                if value:
                    self.draw_voxel_cell(x + c * 26, y + r * 26, self.next_piece.color, size=24)

    def draw_voxel_cell(self, x: int, y: int, color: str, size: int = CELL_SIZE, ghost: bool = False) -> None:
        pad = 3
        if ghost:
            self.canvas.create_rectangle(x + pad, y + pad, x + size - pad, y + size - pad, outline=color, width=3, dash=(4, 3))
            return
        self.canvas.create_rectangle(x + 5, y + 6, x + size - 1, y + size - 1, fill=SHADOW_COLOR, outline="", stipple="gray50")
        self.canvas.create_rectangle(x + pad, y + pad, x + size - pad, y + size - pad, fill=color, outline="#24443D", width=2)
        self.canvas.create_polygon(x + pad, y + pad, x + size - pad, y + pad, x + size - 9, y + 10, x + 9, y + 10, fill="#FFFFFF", outline="", stipple="gray50")
        self.canvas.create_polygon(x + size - pad, y + pad, x + size - pad, y + size - pad, x + size - 10, y + size - 10, x + size - 10, y + 10, fill="#000000", outline="", stipple="gray25")

    def draw_text(self, x: int, y: int, text: str, size: int, anchor: str = "center") -> None:
        font = ("Arial Black", size, "bold")
        self.canvas.create_text(x + 2, y + 2, text=text, fill="#FFFFFF", font=font, anchor=anchor)
        self.canvas.create_text(x, y, text=text, fill=TEXT_COLOR, font=font, anchor=anchor)

    def draw_overlay(self, title: str, subtitle: str) -> None:
        x0 = self.board_x + 22
        y0 = self.board_y + 235
        x1 = self.board_x + COLUMNS * CELL_SIZE - 22
        y1 = y0 + 150
        self.canvas.create_rectangle(x0 + 7, y0 + 8, x1 + 7, y1 + 8, fill="#386B5E", outline="")
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#FFF7BF", outline="#FFFFFF", width=4)
        self.draw_text((x0 + x1) // 2, y0 + 50, title, 24)
        self.draw_text((x0 + x1) // 2, y0 + 103, subtitle, 12)


def main() -> None:
    root = tk.Tk()
    TetrisGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
