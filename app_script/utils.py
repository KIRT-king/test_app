def print_name():
    import os
    import time
    import re
    from pyfiglet import Figlet


    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')


    def clean_ansi_codes(s):
        return re.sub(r'\033\[[0-9;]*m', '', s)


    def print_block_centered(lines, color_codes):
        term_width = os.get_terminal_size().columns
        max_length = max(len(clean_ansi_codes(line)) for line in lines)
        padding = (term_width - max_length) // 2

        for line, color in zip(lines, color_codes):
            print(' ' * padding + color + line + '\033[0m')


    # Цвета и шрифты
    kirt_color = '\033[38;2;155;51;177m'
    app_color = '\033[38;2;135;31;157m'
    dot_color = '\033[38;2;175;95;200m'

    main_font = Figlet(font='dos_rebel')
    dot_font = Figlet(font='dos_rebel')

    # Генерация текста
    kirt_lines = main_font.renderText('KIRT').split('\n')
    app_lines = main_font.renderText('app').split('\n')
    combined = [f"{kirt_color}{k}{app_color}{a}\033[0m" for k, a in zip(kirt_lines, app_lines)]

    # Анимация
    for frame in range(6):
        clear_console()

        # Основной текст
        print_block_centered(
            lines=[clean_ansi_codes(line) for line in combined],
            color_codes=[kirt_color + app_color] * len(combined)
        )

        # Точки
        if frame < 5:
            dots = dot_font.renderText('.' * (frame + 1)).split('\n')
            print_block_centered(dots, [dot_color] * len(dots))

        time.sleep(0.3)

    # Финальный вывод
    clear_console()
    print_block_centered(
        lines=[clean_ansi_codes(line) for line in combined],
        color_codes=[kirt_color + app_color] * len(combined)
    )