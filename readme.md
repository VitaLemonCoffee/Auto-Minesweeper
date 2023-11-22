# Auto Minesweeper

**Warning:** This program involves automatic mouse clicks. Incorrect usage may lead to undefined behavior.

A Minesweeper solver that automatically sweeps the mines based on inference algorithms and light graphic recognition. It does not cheat, but always behaves optimally when logic solution exists.

### How to Run:

```bash
$ python minesw.py
```

### How to Sweep:

1. Open the game at [MS Minesweeper](https://zone.msn.com/gameplayer/gameplayerHTML.aspx?game=msminesweeper).

2. Adjust the mode number (the only parameter) in the `main` function (at the bottom) according to the difficulty:
   - Easy (9x9)       &rarr; 0
   - Medium (16x16)   &rarr; 1
   - Expert (30x16)   &rarr; 2

3. Run the program.

4. Position the cursor at the top-left corner (topmost and leftmost pixel) when the game is fully visible; the sweeping will begin.

5. After completion or an unfortunate failure, you can retry by repeating step 4 or manually stop the program.

**Note:**
- The program may misbehave if:
  - The game is not fully visible.
  - Your screen contains a color similar to the blue of unclicked cells.
  - The game animation runs slowly.