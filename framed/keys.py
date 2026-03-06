import curses
import os


if os.uname().sysname == "Darwin":
    # MacOS likes to be different, I guess
    BACKSPACE = 127
    DELETE = 330
else:
    BACKSPACE = curses.KEY_BACKSPACE
    DELETE = curses.KEY_DC

LEFT = curses.KEY_LEFT
RIGHT = curses.KEY_RIGHT
UP = curses.KEY_UP
DOWN = curses.KEY_DOWN

CTRL_AT = 0
CTRL_A = 1
CTRL_B = 2
CTRL_C = 3
CTRL_D = 4
CTRL_E = 5
CTRL_F = 6
CTRL_G = 7
CTRL_H = 8
CTRL_I = 9
CTRL_J = 10
ENTER = LF = 10
CTRL_K = 11
CTRL_L = 12
CTRL_M = 13
RETURN = CR = 13
CTRL_N = 14
CTRL_O = 15
CTRL_P = 16
CTRL_Q = 17
CTRL_R = 18
CTRL_S = 19
CTRL_T = 20
CTRL_U = 21
CTRL_V = 22
CTRL_W = 23
CTRL_X = 24
CTRL_Y = 25
CTRL_Z = 26

CTRL_OBRACKET = 27
ESCAPE = 27

CTRL_BACKSLASH = 28
CTRL_CBRACKET = 29
CTRL_CARET = 30
CTRL_UNDERSCORE = 31

F1 = curses.KEY_F1
F2 = curses.KEY_F2
F3 = curses.KEY_F3
F4 = curses.KEY_F4
F5 = curses.KEY_F5
F6 = curses.KEY_F6
F7 = curses.KEY_F7
F8 = curses.KEY_F8
F9 = curses.KEY_F9
F10 = curses.KEY_F10
F11 = curses.KEY_F11
F12 = curses.KEY_F12

A = 65
B = 66
C = 67
D = 68
E = 69
F = 70
G = 71
H = 72
I = 73
J = 74
K = 75
L = 76
M = 77
N = 78
O = 79
P = 80
Q = 81
R = 82
S = 83
T = 84
U = 85
V = 86
W = 87
X = 88
Y = 89
Z = 90

a = 97
b = 98
c = 99
d = 100
e = 101
f = 102
g = 103
h = 104
i = 105
j = 106
k = 107
l = 108
m = 109
n = 110
o = 111
p = 112
q = 113
r = 114
s = 115
t = 116
u = 117
v = 118
w = 119
x = 120
y = 121
z = 122

PGUP = curses.KEY_PPAGE
PGDN = curses.KEY_NPAGE

