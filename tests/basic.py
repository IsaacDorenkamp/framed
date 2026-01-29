import curses
import framed


def main(stdscr: curses.window):
    app = framed.Framed(stdscr)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)


