import pygame as pg
from pygame.time import Clock
from pecas import *

pg.init()


class Xadrez:
    def __init__(self, configuracao_inicial=None):
        # Game Flow
        self.tabuleiro = configuracao_inicial or []
        self.vez = 'B'
        self.__passant = []

        # Display Info
        self.__comidas = {'B': [], 'P': []}
        self.__moves = {'B': [], 'P': []}

        # Pygame
        self.running = True
        self.game = True
        self.__marked = None

        self.screen_height = 800
        self.screen_width = int(self.screen_height * 1.5)
        self.screen = None
        self.mouse_pos = (-1, -1)
        self.scroll = 0
        self.move_show_count = 10
        self.imgs = None

    def __repr__(self):
        return [(p.__class.__name__, p.pos) for p in self.tabuleiro]

    def __str__(self):
        return '\n'.join([' '.join(line) for line in self.tabuleiro])

    @staticmethod
    def __criar():
        return [Torre(0, 0, 'P'), Cavalo(0, 1, 'P'), Bispo(0, 2, 'P'), Rainha(0, 3, 'P'),
                Rei(0, 4, 'P'), Bispo(0, 5, 'P'), Cavalo(0, 6, 'P'), Torre(0, 7, 'P'),
                Peao(1, 0, 'P'), Peao(1, 1, 'P'), Peao(1, 2, 'P'), Peao(1, 3, 'P'),
                Peao(1, 4, 'P'), Peao(1, 5, 'P'), Peao(1, 6, 'P'), Peao(1, 7, 'P'),

                Peao(6, 0, 'B'), Peao(6, 1, 'B'), Peao(6, 2, 'B'), Peao(6, 3, 'B'),
                Peao(6, 4, 'B'), Peao(6, 5, 'B'), Peao(6, 6, 'B'), Peao(6, 7, 'B'),
                Torre(7, 0, 'B'), Cavalo(7, 1, 'B'), Bispo(7, 2, 'B'), Rainha(7, 3, 'B'),
                Rei(7, 4, 'B'), Bispo(7, 5, 'B'), Cavalo(7, 6, 'B'), Torre(7, 7, 'B')
                ]

    def copy(self):
        return [peca.__copy__() for peca in self.tabuleiro]

    # Helper Functions

    def cor(self, casa):
        peca = self.casa(casa)
        if peca:
            return peca.cor

    def casa(self, coords):
        for p in self.tabuleiro:
            if p.pos == list(coords):
                return p

    def coluna(self, n):
        col = [None]*8
        for p in self.tabuleiro:
            if p.y == n:
                col[p.x] = p
        return col

    def linha(self, n):
        col = [None]*8
        for p in self.tabuleiro:
            if p.x == n:
                col[p.y] = p
        return col

    def diag(self, offset=0, axis=1):
        if axis == 1:
            x = max(0, -offset)
            y = max(0, offset)
            while x < 8 and y < 8:
                yield self.casa([x, y])
                x += 1
                y += 1
        else:
            x = max(0, offset)
            y = min(7, 7+offset)
            while x < 8 and y >= 0:
                yield self.casa([x, y])
                x += 1
                y -= 1

    @property
    def brancas(self):
        return [peca for peca in self.tabuleiro if peca.cor == 'B']

    @property
    def pretas(self):
        return [peca for peca in self.tabuleiro if peca.cor == 'P']

    def rei(self, cor) -> Rei:
        try:
            r1, r2 = list(filter(Rei.__instancecheck__, self.tabuleiro))
        except ValueError:
            rei = list(filter(Rei.__instancecheck__, self.tabuleiro))[0]
            return rei if rei.cor == cor else None
        else:
            return r1 if r1.cor == cor else r2

    @staticmethod
    def inv_cor(cor):
        return 'P' if cor == 'B' else 'B'

    def scrolled_moves(self, quantity):
        if self.scroll == 0:
            wm = self.__moves['B'][-quantity:]
            bm = self.__moves['P'][-quantity:] if len(self.__moves['B']) == len(self.__moves['P']) else \
                self.__moves['P'][-quantity+1:] + [' ']
        else:
            wm = self.__moves['B'][-quantity + self.scroll:self.scroll]
            if len(self.__moves['B']) == len(self.__moves['P']):
                bm = self.__moves['P'][-quantity + self.scroll:self.scroll]
            elif self.scroll == -1:
                bm = self.__moves['P'][-quantity:]
            else:
                bm = self.__moves['P'][-quantity+1 + self.scroll:self.scroll + 1]
        return wm, bm

    @staticmethod
    def __intercalate(arr1, arr2):
        return sum(zip(arr1, arr2), tuple())

    @staticmethod
    def __font(size):
        return pg.font.SysFont('Calibri', size)

    def __translate(self, origem, destino):
        peca = self.casa(origem)
        outra = self.casa(destino)
        comer = bool(outra)
        letra = {
            'Peao': '',
            'Bispo': 'B',
            'Torre': 'R',
            'Cavalo': 'N',
            'Rainha': 'Q',
            'Rei': 'K'
        }
        final = letra[peca.__class__.__name__]
        if comer:
            final += 'x'
        final += f"{'abcdefgh'[destino[1]]}{8 - destino[0]}"
        return final

    def __is_check(self, _for):
        dic = {
            'P': self.pretas,
            'B': self.brancas,
        }
        king = self.rei(self.inv_cor(_for))
        for peca in dic[_for]:
            if self.__validate_move(peca.pos, king.pos, _for):
                return True
        return False

    def __checker(self, _for):
        """
        :param _for: Turn to check for
        :return:
            0: None
            1: Check
            2: Mate
            3: Drowned King
        """
        dic = {
            'P': self.pretas,
            'B': self.brancas,
        }

        on_check = self.inv_cor(_for)
        deffen = dic[on_check]
        drowned = True
        check = self.__is_check(_for)
        for protect in deffen:
            for move in protect.possiveis(True):
                if self.__validate_move(protect.pos, move, on_check):
                    new = Xadrez(self.copy())
                    new.vez = on_check
                    new.__move(protect.pos, move)
                    if not new.__is_check(_for):
                        drowned = False
                    del new
        if check:
            if drowned:
                return 2
            return 1
        if drowned:
            return 3
        return 0

    # Validations

    def __validate_move(self, origem, destino, vez):
        peca = self.casa(origem)
        outra = self.casa(destino)
        comer = bool(outra)
        x1, y1 = origem
        x2, y2 = destino
        if isinstance(peca, Cavalo):
            path = []
        elif x1 == x2:
            beg = min(y1, y2)
            end = y1 + y2 - beg
            path = self.linha(x1)[beg + 1:end]
        elif y1 == y2:
            beg = min(x1, x2)
            end = x1 + x2 - beg
            path = self.coluna(y1)[beg + 1:end]
        else:
            dx = x2 - x1
            dy = y2 - y1
            if dx == dy:
                offset = y1 - x1
                path = list(self.diag(offset))
                i1 = origem[1] - max(offset, 0)
                i2 = destino[1] - max(offset, 0)
            else:  # dx == -dy
                offset = x1 + y1 - 7
                path = list(self.diag(offset, -1))[::-1]
                i1 = origem[1] - max(offset, 0)
                i2 = destino[1] - max(offset, 0)
            beg = min(i1, i2)
            end = i1 + i2 - beg
            path = path[beg + 1:end]

        if len(set(path)) > 1 or (path and None not in path) or self.cor(destino) == vez or self.cor(origem) != vez:
            return False

        valido = peca.validate(destino, comer)
        if valido:
            delta = y2 - y1
            if isinstance(peca, Rei):
                if abs(delta) == 2 and not peca.moved:
                    if peca.cor == 'B':
                        try:
                            if delta == 2 and not self.casa([7, 7]).moved:
                                path = self.linha(7)[5:7]
                            elif delta == -2 and not self.casa([7, 0]).moved:
                                path = self.linha(7)[1:4]
                            else:
                                return False
                            if len(set(path)) == 1 and None in path:
                                return 'roque'
                            return False
                        except AttributeError:
                            return False
                    else:
                        try:
                            if delta == 2 and not self.casa([0, 7]).moved:
                                path = self.linha(0)[5:7]
                            elif delta == -2 and not self.casa([0, 0]).moved:
                                path = self.linha(0)[1:4]
                            else:
                                return False
                            if len(set(path)) == 1 and None in path:
                                return 'roque'
                            return False
                        except AttributeError:
                            return False
            elif isinstance(peca, Peao):
                if delta == 0 and comer:
                    return False

        return valido

    def __validate_passant(self, origem, destino):
        comer = [origem[0], destino[1]]
        cor1 = self.cor(origem)
        cor2 = self.cor(comer)
        falsy = [
            not isinstance(self.casa(origem), Peao),
            not isinstance(self.casa(comer), Peao),
            cor1 == cor2,
            None in (cor1, cor2),
            self.casa(destino) is not None,
            self.casa(comer) not in self.__passant
        ]
        if any(falsy):
            return False
        return 'passant'

    def __validate_not_check_move(self, origem, destino):
        new = Xadrez(list(self.copy()))
        turn = new.cor(origem)
        new.vez = turn
        new.__move(origem, destino)
        return not new.__is_check(self.inv_cor(turn))

    # Moving

    def __move(self, origem, destino):
        notation = self.__translate(origem, destino)
        self.__passant = []
        peca = self.casa(origem)
        outra = self.casa(destino)
        cor = self.cor(origem)

        # Color Validation
        if cor != self.vez:
            self.__text("Não é sua vez")
            return False
        elif cor == self.cor(destino):
            self.__text("Nao pode comer sua peça!", (255, 0, 0))
            return False

        # Handle Comer
        if outra is not None:
            self.__comidas[self.vez].append(outra)
            self.tabuleiro.remove(outra)

        if isinstance(peca, Rei) and abs(origem[1] - destino[1]) == 2:  # Roque
            cor = self.cor(origem)
            modo = 'C' if destino[1] > origem[1] else 'L'
            self.__move_roque(cor + modo)
        elif isinstance(peca, Peao) and abs(origem[1] - destino[1]) == 1 and outra is None:  # Passant
            self.__comer_passant(origem, destino)
            notation = 'x' + notation
        else:  # Movimento normal
            peca.move(*destino)
            if isinstance(peca, Peao) and abs(destino[0] - origem[0]) == 2:
                self.__passant.append(peca)

        # Promotion
        if isinstance(peca, Peao) and destino[0] in (0, 7):
            if self.screen:
                new = self.__promote(self.cor(destino))
                classe = {
                    'Rainha': Rainha,
                    'Bispo': Bispo,
                    'Cavalo': Cavalo,
                    'Torre': Torre,
                }
                self.tabuleiro.append(classe[new](*destino, self.cor(destino)))
                self.tabuleiro.remove(peca)
                self.blit()
                nota = {'Rainha': 'Q', 'Bispo': 'B', 'Torre': 'R', 'Cavalo': 'N'}
                notation += f'={nota[new]}'
            else:
                self.tabuleiro.append(Supreme(*destino, self.cor(origem)))
                self.tabuleiro.remove(peca)

        # Check and Mate
        if self.screen:
            state = self.__checker(self.vez)
            if state:
                self.blit()
                pg.display.update()
            if state == 2:
                self.__text("Cheque Mate", (255, 0, 0))
                notation += '++'
                self.game = False
            elif state == 1:
                self.__text('Cheque', (250, 200, 0))
                notation += '+'
            elif state == 3:
                self.__text("Rei Afogado")
            self.__moves[self.vez].append(notation)

        self.vez = self.inv_cor(self.vez)
        return True

    def __move_roque(self, _id):
        x = 7 if _id[0] == 'B' else 0
        para = -1 if _id[1] == 'L' else 1
        ty = 0 if _id[1] == 'L' else 7

        rei = self.rei(_id[0])
        torre = self.casa([x, ty])
        if rei.moved or torre.moved:
            return False

        try:
            rei.move(x, 4 + 2 * para)
            torre.move(x, 4 + para)
        except AttributeError:
            breakpoint()

    def __comer_passant(self, origem, destino):
        comer = [origem[0], destino[1]]
        peca = self.casa(origem)
        outra = self.casa(comer)
        self.__comidas[self.cor(origem)].append(outra)
        peca.move(*destino)
        self.tabuleiro.remove(outra)

    # Pygame

    def __moves_box(self, width, height):
        rows = self.move_show_count + 1
        surface: pg.Surface = pg.Surface((width, height))
        pg.draw.rect(surface, (0, 0, 0), ((0, 0), (width, height)))  # Black Outline
        pg.draw.rect(surface, (127, 127, 127), ((2, 2), (width // 2 - 3, height // rows - 3)))  # Top Left
        pg.draw.rect(surface, (127, 127, 127), ((width // 2 + 1, 2), (width // 2 - 3, height // rows - 3)))  # Top Right
        pg.draw.rect(surface, (127, 127, 127),
                     ((2, height // rows + 1), (width // 2 - 3, height * (rows - 1) // rows - 3)))  # Bottom Left
        pg.draw.rect(surface, (127, 127, 127),
                     ((width // 2 + 1, height // rows + 1),
                      (width // 2 - 3, height * (rows - 1) // rows - 3)))  # Bottom Right

        txt_brancas = self.__font(30).render("Brancas", True, (255, 255, 255))
        txt_pretas = self.__font(30).render("Pretas", True, (0, 0, 0))
        surface.blit(txt_brancas,
                     ((width / 2 - txt_brancas.get_width()) // 2, (height / rows - txt_brancas.get_height()) // 2))
        surface.blit(txt_pretas,
                     ((width * 3 / 2 - txt_brancas.get_width()) // 2, (height / rows - txt_brancas.get_height()) // 2))

        moves = self.__intercalate(*self.scrolled_moves(rows-1))
        for i, move in enumerate(moves):
            #  Terminar Design;
            cor = (255 * (1 - i % 2),) * 3
            w = 2 if i % 2 == 0 else width // 2 + 1
            h = 2 + height * (i // 2 + 1) // rows
            img = self.__font(35).render(move, True, cor)
            surface.blit(img, (w, h))

        return surface

    def __eaten_box(self, size, grid_size=4):
        surface: pg.Surface = pg.Surface((size, size))
        pg.draw.rect(surface, (0, 0, 0), ((0, 0), (size - 4, size - 4)))  # Black Outline
        pg.draw.rect(surface, (127, 127, 127), ((2, 2), (size // 2 - 3, size - 4)))  # Left
        pg.draw.rect(surface, (127, 127, 127), ((size // 2 + 1, 2), (size // 2 - 3, size - 4)))  # Right
        classes = ['Rei', 'Rainha', 'Torre', 'Cavalo', 'Bispo', 'Peao']
        img_size = size // (grid_size * 2)
        for i, peca in enumerate(sorted(self.__comidas['P'], key=lambda p: classes.index(p.__class__.__name__))):
            rel_w = i % grid_size
            rel_h = i // grid_size
            img = pg.transform.scale(self.imgs['B'][peca.__class__.__name__], (img_size, img_size))
            surface.blit(img, (img_size * rel_w + 2, img_size * rel_h + 1))
        for i, peca in enumerate(sorted(self.__comidas['B'], key=lambda p: classes.index(p.__class__.__name__))):
            rel_w = i % 3
            rel_h = i // 3
            img = pg.transform.scale(self.imgs['P'][peca.__class__.__name__], (img_size, img_size))
            surface.blit(img, (size // 2 + img_size * rel_w + 3, img_size * rel_h + 1))
        return surface

    def blit(self, force=True):
        cor = 255
        for x in range(8):
            for y in range(8):
                if force:
                    self.__draw_rect(self.screen, x, y, (cor, cor, cor))
                cor = 400 - cor
            cor = 400 - cor

        for peca in self.tabuleiro:
            img = self.imgs[peca.cor][peca.__class__.__name__]
            self.screen.blit(img, (peca.y * 100, peca.x * 100))

        pg.draw.rect(self.screen, (200, 200, 200),
                     ((self.screen_height, 0), (self.screen_width - self.screen_height, self.screen_height)))
        self.screen.blit(self.__moves_box(self.screen_height // 3, self.screen_height // 2),
                         (self.screen_height * 8.1 // 8, self.screen_height // 16))
        self.screen.blit(self.__eaten_box(self.screen_height // 3, 3),
                         (self.screen_height * 8.1 // 8, self.screen_height * 10 // 16))

    def __text(self, text, color=(0, 0, 0)):
        img = self.__font(95).render(text, True, color)
        img_w, img_h = img.get_size()
        self.screen.blit(img, ((self.screen_width - img_w) // 2, (self.screen_height - img_h) // 2))
        pg.display.update()
        pos = self.__wait_for_click()
        self.blit()
        return pos

    def __mark(self, x, y):
        if self.__marked:
            self.blit()
        peca = self.casa([x, y])
        if peca is None:
            return
        self.__marked = [[x, y], []]
        self.__draw_rect(self.screen, y, x, (100, 150, 250))

        for x1, y1 in peca.possiveis(True):
            comer = self.casa([x1, y1]) is not None
            if (y1 != y and isinstance(peca, Peao) and (not comer) and x not in (3, 4)) \
                    or (y1 == y and isinstance(peca, Peao) and comer):
                continue
            elif isinstance(peca, Peao) and y1 != y and x in (3, 4) and not comer:
                val = self.__validate_passant([x, y], [x1, y1])
                comer = True
            else:
                val = self.__validate_move((x, y), (x1, y1), self.cor([x, y]))
                if val:
                    val = val if self.__validate_not_check_move((x, y), (x1, y1)) else False
            if val:
                if peca.cor != self.vez:
                    cor = (250, 250, 100)  # Amarelo
                elif val == 'roque':
                    cor = (200, 100, 250)  # Roxo
                elif comer:
                    cor = (250, 100, 150)  # Vermelho
                else:
                    cor = (100, 250, 150)  # Verde
                self.__draw_rect(self.screen, y1, x1, cor)
                self.__marked[1].append((x1, y1))

    @staticmethod
    def __draw_rect(screen, x, y, color):
        pg.draw.rect(screen, (0, 0, 0), ((x * 100, y * 100), (100, 100)))
        pg.draw.rect(screen, color, ((x * 100 + 1, y * 100 + 1), (98, 98)))

    def __wait_for_click(self):
        while self.running:
            for evt in pg.event.get():
                if evt.type == pg.QUIT:
                    self.running = False
                    self.game = False
                    return -1, -1
                elif evt.type == pg.MOUSEBUTTONDOWN:
                    return evt.pos

    def __promote(self, color):
        self.screen.fill((255, 255, 255))
        pg.draw.rect(self.screen, (0, 0, 0), ((self.screen_width // 2 - 1, 0), (2, self.screen_height)))
        pg.draw.rect(self.screen, (0, 0, 0), ((0, self.screen_height // 2 - 1), (self.screen_width, 2)))
        possibs = ['Rainha', 'Cavalo', 'Bispo', 'Torre']
        for i, peca in enumerate(possibs):
            img = pg.transform.scale(self.imgs[color][peca], (self.screen_width // 8, self.screen_height // 8))
            self.screen.blit(img, (
                (i // 2) * (self.screen_width // 2) + 3 * self.screen_width // 16,
                (i % 2) * (self.screen_height // 2) + 3 * self.screen_height // 16))
        pg.display.update()
        try:
            x, y = self.__wait_for_click()
        except TypeError:
            return
        return possibs[(x * 2) // self.screen_width * 2 + (y * 2) // self.screen_height]

    def __start_screen(self):
        self.screen.fill((255, 255, 255))
        while self.running:
            w = self.screen_width * 1 // 3
            h = self.screen_height * 1 // 3
            pg.draw.rect(self.screen, (100, 100, 100), ((w, h), (self.screen_width // 3, self.screen_height // 3)))
            w, h = self.__text("Iniciar")
            if abs(w - self.screen_width / 2) < 100 and abs(h - self.screen_height / 2) < 100:
                self.tabuleiro = self.__criar()
                return

    def event_listener(self):
        scrolled = False
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                self.running = False
                self.game = False
            elif evt.type == pg.MOUSEBUTTONDOWN:
                w = self.mouse_pos[0] // 100
                h = self.mouse_pos[1] // 100
                if self.__marked:
                    if (h, w) in self.__marked[1]:
                        ok = self.__move(self.__marked[0], [h, w])
                        if ok:
                            self.blit()
                        self.__marked = None
                    elif self.casa([h, w]) is not None:
                        self.__mark(h, w)
                    else:
                        self.blit()
                        self.__marked = None
                else:
                    self.__mark(h, w)
            elif evt.type == pg.MOUSEMOTION:
                self.mouse_pos = evt.pos
            elif evt.type == pg.MOUSEWHEEL and not scrolled:
                self.scroll = max(min(self.scroll - evt.y, 0), min(-len(self.__moves['B']) + self.move_show_count, 0))
                scrolled = True

    def loop(self):
        self.screen: pg.Surface = pg.display.set_mode((self.screen_width, self.screen_height))
        self.imgs = {
            'P': {name: pg.transform.scale(pg.image.load(f'./assets/Preto/{name}.png'), (100, 100))
                  for name in ['Peao', 'Bispo', 'Torre', 'Cavalo', 'Rei', 'Rainha']},
            'B': {name: pg.transform.scale(pg.image.load(f'./assets/Branco/{name}.png'), (100, 100))
                  for name in ['Peao', 'Bispo', 'Torre', 'Cavalo', 'Rei', 'Rainha']}
        }
        pg.display.set_caption("Chess Game")
        pg.display.set_icon(self.imgs['P']['Rei'])
        clock = Clock()

        while self.running:
            self.__start_screen()
            self.blit()
            while self.game:
                self.blit(False)
                self.event_listener()
                pg.display.update()
                clock.tick(100)


if __name__ == '__main__':
    Xadrez().loop()
