# Voxel Tetris

A keyboard-controlled Tetris game written in Python with `tkinter`. The visual style uses bright grass tones, chunky shadows, and toy-like voxel blocks inspired by the friendly Crossy Road aesthetic.

## Run

```bash
python main.py
```

`tkinter` is included with most desktop Python installations. On minimal Linux systems, install the OS package for Tk support if the window cannot start.

## Controls

| Key | Action |
| --- | --- |
| Left / Right or A / D | Move the current piece |
| Down or S | Soft drop |
| Up, W, or X | Rotate |
| Space | Hard drop |
| P | Pause / resume |
| R | Restart after game over |

## Gameplay features

- Seven-bag random tetromino generation.
- Score, line, and level tracking.
- Increasing fall speed as levels advance.
- Ghost piece preview for easier hard drops.
- Next-piece preview panel.
