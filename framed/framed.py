import curses


class Framed:
    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__running = True

    def run(self):
        curses.set_escdelay(25)
        curses.raw()

        while self.__running:
            ch = self.__stdscr.getch()
            if ch == -1:
                continue
            elif ch == 3:
                # Ctrl-C
                self.__running = False
            else:
                pass

