"""Tk interface for playing four in a row and comparing the search agents."""
import tkinter as tk
from tkinter import font as tkfont, ttk

from agents import AGENTS
from game import Board, coordinates, example, winning_lines
from play import choose

NAVY = '#12202b'
TILE = '#1b2f3d'
TILE_EDGE = '#2e4757'
TEAL = '#5fd0bf'
AMBER = '#f2a750'
CREAM = '#f6f3ec'
PALE = '#fffdf8'
SILVER = '#c5d3d9'
MUTED = '#41525e'
RULE = '#d9d3c4'
ACCENT = '#17695f'
NAMES = {'human': 'Human', 'minimax': 'Minimax', 'mcts': 'MCTS'}


def style_controls(root, font):
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Player.TCombobox', padding=(5, 6), arrowcolor=NAVY, bordercolor=RULE)
    style.map('Player.TCombobox', fieldbackground=[('readonly', PALE)],
              foreground=[('readonly', NAVY)], selectbackground=[('readonly', PALE)],
              selectforeground=[('readonly', NAVY)])
    for name, bg, fg, active in (
        ('Action.TButton', '#e7e2d6', NAVY, '#d9d3c4'),
        ('Primary.TButton', ACCENT, PALE, '#10564e'),
        ('Segment.TRadiobutton', '#e7e2d6', NAVY, '#d9d3c4'),
    ):
        style.configure(name, background=bg, foreground=fg, font=(font, 12, 'bold'),
                        bordercolor=RULE, lightcolor=bg, darkcolor=bg, relief='flat',
                        borderwidth=1, padding=(5, 6), anchor='center', focuscolor=fg)
        if name.endswith('TRadiobutton'):
            style.layout(name, style.layout('TButton'))
        colors = [('disabled', CREAM), ('selected', NAVY), ('active', active)]
        style.map(name, background=colors, lightcolor=colors, darkcolor=colors,
                  foreground=[('disabled', MUTED), ('selected', PALE)],
                  focuscolor=[('selected', PALE)], bordercolor=[('focus', ACCENT)])


class GameWindow:
    def __init__(self, root):
        self.root = root
        root.title('Four in a row')
        root.configure(bg=NAVY)
        root.minsize(430, 580)
        root.geometry('980x640')
        families = set(tkfont.families(root))
        self.heading = next((f for f in ('Space Grotesk', 'Avenir Next', 'Helvetica')
                             if f in families), 'TkDefaultFont')
        self.font = 'Inter' if 'Inter' in families else tkfont.nametofont('TkDefaultFont').actual('family')
        style_controls(root, self.font)
        self.size = tk.IntVar(value=4)
        self.players = {'X': tk.StringVar(value='Human'), 'O': tk.StringVar(value='MCTS')}
        self.ai_timer = None
        self.status = tk.StringVar()
        self.detail = tk.StringVar()
        self.compact = None
        self.hover = None
        self.focus_cell = 0
        self.keyboard = False

        self.stage = tk.Frame(root, bg=NAVY)
        self.intro = tk.Frame(self.stage, bg=NAVY)
        self.eyebrow = self.label(self.intro, 'CSE 352  /  LIVE DEMO', 11, TEAL, bold=True)
        self.title = self.label(self.intro, 'Four in a Row', 36, CREAM, heading=True, bold=True)
        self.subtitle = self.label(self.intro, '', 15, SILVER)
        self.turn_row = tk.Frame(self.intro, bg=NAVY)
        self.turn = self.label(self.turn_row, '', 17, TEAL, bold=True, textvariable=self.status)
        self.flow_button = ttk.Button(self.turn_row, width=8, style='Primary.TButton',
                                      command=self.toggle_play)
        self.note = self.label(self.intro, '', 12, SILVER, textvariable=self.detail, justify='left')
        for widget in (self.eyebrow, self.title, self.subtitle):
            widget.pack(anchor='w')
        self.turn_row.pack(anchor='w', pady=(24, 2))
        self.turn.pack(side='left')
        self.flow_button.pack(side='left', padx=(12, 0))
        self.note.pack(anchor='w')

        self.board_area = tk.Frame(self.stage, bg=NAVY)
        self.canvas = tk.Canvas(self.board_area, width=1, height=1, bd=0, bg=NAVY,
                                takefocus=True, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.move_count = self.label(self.board_area, '', 11, SILVER)
        self.move_count.pack(anchor='e', padx=6)

        self.controls = tk.Frame(root, bg=CREAM, padx=16, pady=10)
        self.settings = tk.Frame(self.controls, bg=CREAM)
        self.analysis = tk.Frame(self.controls, bg=CREAM)
        self.setup_title = self.label(self.settings, 'Game setup', 15, NAVY, bold=True, heading=True)
        self.analysis_title = self.label(self.analysis, 'Move analysis', 15, NAVY, bold=True, heading=True)
        self.selectors = []
        self.selector('Board size', self.size, [(n, f'{n} × {n}') for n in (4, 5, 6)], self.reset)
        for mark, player in self.players.items():
            group = self.selector_group(f'{mark} player')
            picker = ttk.Combobox(group, textvariable=player, values=tuple(NAMES.values()),
                                  state='readonly', width=6, font=(self.font, 12),
                                  style='Player.TCombobox')
            picker.pack(fill='x')
            picker.bind('<<ComboboxSelected>>', self.players_changed)
        self.restart = ttk.Button(self.settings, text='Restart', width=7,
                                  style='Action.TButton', command=self.reset)
        self.compare_button = ttk.Button(self.analysis, text='Compare moves', width=1,
                                         style='Primary.TButton', command=self.compare)
        self.actions = [self.compare_button]
        for tactic in ('win', 'block'):
            self.actions.append(ttk.Button(self.analysis, text=f'Load {tactic}', width=1,
                                           style='Action.TButton',
                                           command=lambda t=tactic: self.reset(t)))
        self.divider = tk.Frame(self.controls, bg=RULE, width=1, height=1)
        self.controls.pack(side='bottom', fill='x')
        self.stage.pack(fill='both', expand=True)
        root.bind('<Configure>', self.layout)
        self.stage.bind('<Configure>', self.position_stage)
        self.canvas.bind('<Configure>', lambda e: self.draw())
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<Leave>', lambda e: self.set_hover(None))
        self.canvas.bind('<FocusIn>', self.focus_in)
        self.canvas.bind('<FocusOut>', lambda e: self.draw())
        for key in ('Left', 'Right', 'Up', 'Down', 'space', 'Return'):
            self.canvas.bind(f'<{key}>', self.keypress)
        self.reset()

    def label(self, parent, text, size, color, *, bold=False, heading=False, **options):
        family = self.heading if heading else self.font
        return tk.Label(parent, text=text, bg=parent['bg'], fg=color, bd=0,
                        padx=0, pady=0, font=(family, size, 'bold' if bold else 'normal'),
                        **options)

    def selector_group(self, title):
        group = tk.Frame(self.settings, bg=CREAM)
        self.selectors.append(group)
        self.label(group, title, 11, MUTED).pack(anchor='w', pady=(0, 3))
        return group

    def selector(self, title, variable, options, command=None):
        group = self.selector_group(title)
        strip = tk.Frame(group, bg=CREAM)
        strip.pack(fill='x')
        for col, (value, caption) in enumerate(options):
            strip.columnconfigure(col, weight=1, uniform='option')
            button = ttk.Radiobutton(strip, text=caption, value=value, variable=variable,
                                     style='Segment.TRadiobutton', command=command, width=1)
            button.grid(row=0, column=col, sticky='ew', padx=(2 if col else 0, 0))

    def layout(self, event):
        if event.widget != self.root:
            return
        width, height = self.root.winfo_width(), self.root.winfo_height()
        compact = width < 810 or height > width
        if compact == self.compact:
            return
        self.compact = compact
        for widget in (self.settings, self.analysis, self.divider, self.setup_title,
                       self.analysis_title, *self.selectors, self.restart, *self.actions):
            widget.grid_forget()
        for col in (0, 2):
            self.controls.columnconfigure(col, weight=0, uniform='')
        self.controls.columnconfigure(0, weight=8, uniform='' if compact else 'strip')
        self.settings.grid(row=0, column=0, sticky='nsew')
        if compact:
            self.divider.grid(row=1, column=0, sticky='ew', pady=6)
            self.analysis.grid(row=2, column=0, sticky='ew')
        else:
            self.controls.columnconfigure(2, weight=5, uniform='strip')
            self.divider.grid(row=0, column=1, sticky='ns', padx=20)
            self.analysis.grid(row=0, column=2, sticky='nsew')
            self.setup_title.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
            self.analysis_title.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
        for col, group in enumerate(self.selectors):
            self.settings.columnconfigure(col, weight=1)
            group.grid(row=1, column=col, sticky='sew', padx=(0, 8))
        self.restart.grid(row=1, column=len(self.selectors), sticky='s')
        self.analysis.rowconfigure(1, weight=1)
        for col, button in enumerate(self.actions):
            self.analysis.columnconfigure(col, weight=4 if col == 0 else 3, uniform='action')
            button.grid(row=1, column=col, sticky='sew', padx=(5 if col else 0, 0))
        self.position_stage()

    def position_stage(self, event=None):
        w, h = self.stage.winfo_width(), self.stage.winfo_height()
        if min(w, h) < 2:
            return
        if self.compact:
            margin = 18
            self.title.configure(font=(self.heading, 27, 'bold'))
            self.turn_row.pack_configure(pady=(7, 0))
            self.subtitle.configure(wraplength=0)
            self.note.configure(wraplength=w - 2 * margin)
            # Reserve space for a second line so a new hint cannot move the grid.
            intro_height = self.intro.winfo_reqheight() + 20
            side = max(1, min(w - 2 * margin, h - intro_height - 44))
            top = max(10, (h - intro_height - side - 20) // 2)
            self.intro.place(x=(w-side)//2, y=top, rely=0, anchor='nw',
                             width=w - (w-side)//2 - margin)
            self.board_area.place(x=(w-side)//2, y=top+intro_height, rely=0, anchor='nw',
                                  width=side, height=side+20)
        else:
            margin = max(28, int(w * 0.055))
            self.title.configure(font=(self.heading, 38, 'bold'))
            self.turn_row.pack_configure(pady=(28, 2))
            content = min(1200, w - 2 * margin)
            side = min(h - 68, int(content * 0.56))
            text_width = content - side - 32
            self.note.configure(wraplength=text_width)
            self.subtitle.configure(wraplength=text_width, justify='left')
            self.intro.place(x=(w-content)//2, y=0, rely=0.5, anchor='w', width=text_width)
            self.board_area.place(x=(w+content)//2, y=0, rely=0.5, anchor='e',
                                  width=side, height=side+20)

    def reset(self, tactic=None):
        self.phase = 'ready'
        n = self.size.get()
        self.board = example(n, tactic) if tactic else Board(n)
        self.hints = {}
        self.last_move = self.hover = None
        self.canvas.configure(cursor='')
        self.focus_cell = 0
        self.keyboard = False
        self.detail.set({'win': 'Find the move that completes four Xs.',
                         'block': 'Block the line of three Os.'}.get(
                             tactic, 'Four in a line wins.'))
        self.start_turn()

    def players_changed(self, event):
        self.set_hover(None)
        self.start_turn()

    def toggle_play(self):
        if self.board.outcome:
            return
        self.phase = 'paused' if self.phase == 'playing' else 'playing'
        self.set_hover(None)
        self.start_turn()

    def can_compare(self):
        return not self.board.outcome and (self.phase != 'playing' or self.human_turn())

    def human_turn(self):
        return (self.phase == 'playing' and not self.board.outcome
                and self.players[self.board.turn].get() == 'Human')

    def start_turn(self):
        if self.ai_timer is not None:
            self.root.after_cancel(self.ai_timer)
            self.ai_timer = None
        self.subtitle.configure(text=f"X · {self.players['X'].get()}    O · {self.players['O'].get()}")
        self.refresh()
        if self.phase == 'playing' and not self.board.outcome and not self.human_turn():
            self.ai_timer = self.root.after(450, self.ai_move)

    def ai_move(self):
        self.ai_timer = None
        player = self.players[self.board.turn].get()
        if self.phase == 'playing' and not self.board.outcome and player != 'Human':
            self.apply_move(choose(self.board, player.lower()))

    def refresh(self):
        outcome = self.board.outcome
        mark = self.board.turn
        if outcome:
            title = 'Draw' if outcome == 'draw' else f'{outcome} wins!'
        elif self.phase == 'ready':
            title = 'Ready to play'
        elif self.phase == 'paused':
            title = f'Paused · {mark} to play'
        elif self.human_turn():
            title = f'Your turn · {mark}'
        else:
            title = f'{self.players[mark].get()} to play · {mark}'
        if outcome:
            self.flow_button.pack_forget()
        else:
            caption = {'ready': 'Start', 'playing': 'Pause', 'paused': 'Resume'}[self.phase]
            self.flow_button.configure(text=caption)
            self.flow_button.pack(side='left', padx=(12, 0))
        self.status.set(title)
        self.turn.configure(fg=AMBER if (outcome or self.board.turn) == 'O' else TEAL)
        self.move_count.configure(text=f'{(self.board.x | self.board.o).bit_count()} / '
                                       f'{self.board.size ** 2} squares played')
        self.compare_button.state(['!disabled'] if self.can_compare() else ['disabled'])
        self.draw()

    def geometry(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        extent = max(1, min(w, h) - 32)
        return (w - extent) / 2 + 7, (h - extent) / 2 + 7, extent / self.board.size

    def cell_at(self, event):
        left, top, side = self.geometry()
        col = int((event.x - left) // side)
        row = int((event.y - top) // side)
        if 0 <= row < self.board.size and 0 <= col < self.board.size:
            return row * self.board.size + col

    def draw(self):
        canvas = self.canvas
        canvas.delete('all')
        left, top, side = self.geometry()
        n = self.board.size
        for i in range(n):
            center = (i + 0.5) * side
            for x, y in ((left + center, top - 12), (left - 12, top + center)):
                canvas.create_text(x, y, text=i+1, fill=SILVER, font=(self.font, 10))
        wins = 0
        if self.board.outcome in ('X', 'O'):
            marks = self.board.x if self.board.outcome == 'X' else self.board.o
            for line in winning_lines(n):
                if marks & line == line:
                    wins |= line
        for i in range(n * n):
            row, col = divmod(i, n)
            x, y = left + side * col, top + side * row
            names = [NAMES[name] for name, move in self.hints.items() if move == i]
            focus = self.keyboard and self.canvas.focus_get() == canvas and i == self.focus_cell
            bg, outline = TILE, TILE_EDGE
            if wins & (1 << i):
                bg, outline = ('#214c4d', TEAL) if self.board.outcome == 'X' else ('#59422f', AMBER)
            elif names:
                bg, outline = '#214c4d', TEAL
            elif self.hover == i:
                bg, outline = '#274352', SILVER
            gap = max(2, round(side * 0.033))
            canvas.create_rectangle(x+gap, y+gap, x+side-gap, y+side-gap, fill=bg,
                                    outline=CREAM if focus else outline, width=2 if focus else 1)
            cx, cy = x + side/2, y + side/2
            mark = self.board.cell(i)
            if mark != '.':
                canvas.create_text(cx, cy, text=mark, fill=TEAL if mark == 'X' else AMBER,
                                   font=(self.heading, -max(12, round(side*0.56)), 'bold'))
            elif names:
                canvas.create_text(cx, cy, text='Both' if len(names) > 1 else names[0],
                                   fill=TEAL, font=(self.font, -max(9, min(16, int(side/4.7))), 'bold'))
            if i == self.last_move:
                dot = max(2, side * 0.032)
                canvas.create_oval(x+side-gap-4*dot, y+gap+2*dot,
                                   x+side-gap-2*dot, y+gap+4*dot,
                                   fill=TEAL if mark == 'X' else AMBER, outline='')

    def set_hover(self, move):
        if not self.human_turn() or move is None or self.board.cell(move) != '.':
            move = None
        if self.hover != move:
            self.hover = move
            self.canvas.configure(cursor='hand2' if move is not None else '')
            self.draw()

    def motion(self, event):
        self.set_hover(self.cell_at(event))

    def focus_in(self, event):
        self.keyboard = True
        self.draw()

    def keypress(self, event):
        self.keyboard = True
        if event.keysym in ('space', 'Return'):
            self.play(self.focus_cell)
        else:
            n = self.board.size
            row, col = divmod(self.focus_cell, n)
            dr, dc = {'Up': (-1, 0), 'Down': (1, 0), 'Left': (0, -1), 'Right': (0, 1)}[event.keysym]
            self.focus_cell = max(0, min(n-1, row+dr)) * n + max(0, min(n-1, col+dc))
        self.draw()
        return 'break'

    def click(self, event):
        move = self.cell_at(event)
        if move is not None:
            self.canvas.focus_set()
            self.keyboard = False
            self.focus_cell = move
            self.play(move)

    def play(self, move):
        if self.human_turn() and self.board.cell(move) == '.':
            self.apply_move(move)

    def apply_move(self, move):
        mark = self.board.turn
        player = self.players[mark].get()
        self.hints = {}
        self.set_hover(None)
        self.board = self.board.play(move)
        self.last_move = move
        row, col = coordinates(self.board.size, move)
        self.detail.set(f'{mark} ({player}) played row {row}, column {col}.')
        if self.board.outcome == 'draw':
            self.detail.set('Board full. Restart to play again.')
        elif self.board.outcome:
            self.detail.set('Winning squares highlighted. Restart to play again.')
        self.start_turn()

    def compare(self):
        if not self.can_compare():
            return
        self.detail.set('Comparing moves…')
        self.root.update_idletasks()
        self.hints = {name: choose(self.board, name) for name in AGENTS}
        self.detail.set('   ·   '.join(f'{NAMES[name]} {coordinates(self.board.size, move)}'
                                      for name, move in self.hints.items()))
        self.draw()


if __name__ == '__main__':
    root = tk.Tk()
    GameWindow(root)
    root.mainloop()
