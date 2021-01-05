import pygame as pg
from pygame.time import Clock
from pecas import *

pg.init()


class Xadrez:
    def __init__(self, configuracao_inicial=None):
        self.tabuleiro = configuracao_inicial or self.__criar()
        self.__comidas = {'B': [], 'P': []}
        self.vez = 'B'
        self.__passant = []

        # Pygame
        self.running = True
        self.__previous = []
        self.__marked = None

        self.screen_size = 800
        self.screen = None
        self.imgs = None

    def __repr__(self):
        return [(p.__class.__name__, p.pos) for p in self.tabuleiro]

    def __str__(self):
        return '\n'.join([' '.join(line) for line in self.tabuleiro])

    @staticmethod
    def __criar():
        return [Torre(0, 0, 'P'), Cavalo(0, 1, 'P'), Bispo(0, 2, 'P'), Rei(0, 3, 'P'),
                Rainha(0, 4, 'P'), Bispo(0, 5, 'P'), Cavalo(0, 6, 'P'), Torre(0, 7, 'P'),
                Peao(1, 0, 'P'), Peao(1, 1, 'P'), Peao(1, 2, 'P'), Peao(1, 3, 'P'),
                Peao(1, 4, 'P'), Peao(1, 5, 'P'), Peao(1, 6, 'P'), Peao(1, 7, 'P'),

                Peao(6, 0, 'B'), Peao(6, 1, 'B'), Peao(6, 2, 'B'), Peao(6, 3, 'B'),
                Peao(6, 4, 'B'), Peao(6, 5, 'B'), Peao(6, 6, 'B'), Peao(6, 7, 'B'),
                Torre(7, 0, 'B'), Cavalo(7, 1, 'B'), Bispo(7, 2, 'B'), Rei(7, 3, 'B'),
                Rainha(7, 4, 'B'), Bispo(7, 5, 'B'), Cavalo(7, 6, 'B'), Torre(7, 7, 'B')
                ]

    def copy(self):
        return [peca.__copy__() for peca in self.tabuleiro]

    # Getters

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
        r1, r2 = list(filter(Rei.__instancecheck__, self.tabuleiro))
        return r1 if r1.cor == cor else r2

    @staticmethod
    def inv_cor(cor):
        return 'P' if cor == 'B' else 'B'

    # Outros

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
                        if delta == 2 and not self.casa([7, 7]).moved:
                            path = self.linha(7)[4:7]
                        elif delta == -2 and not self.casa([7, 0]).moved:
                            path = self.linha(7)[1:3]
                        else:
                            return False
                        if len(set(path)) == 1 and None in path:
                            return 'roque'
                        return False
                    else:
                        if delta == 2 and not self.casa([0, 7]).moved:
                            path = self.linha(0)[4:7]
                        elif delta == -2 and not self.casa([0, 0]).moved:
                            path = self.linha(0)[1:3]
                        else:
                            return False
                        if len(set(path)) == 1 and None in path:
                            return 'roque'
                        return False
            elif isinstance(peca, Peao):
                if delta == 0 and comer:
                    return False

        return valido

    def __move(self, origem, destino):
        self.__passant = []
        peca = self.casa(origem)
        outra = self.casa(destino)
        if self.cor(origem) != self.vez:
            self.__text("Não é sua vez")
            return False

        if outra is not None:  # Handle Comer
            self.__comidas[self.vez].append(outra)
            self.tabuleiro.remove(outra)

        if isinstance(peca, Rei) and abs(origem[1] - destino[1]) == 2:  # Roque
            cor = self.cor(origem)
            modo = 'L' if destino[1] > origem[1] else 'C'
            self.__move_roque(cor + modo)
        elif isinstance(peca, Peao) and abs(origem[1] - destino[1]) == 1 and outra is None:  # Passant
            self.__comer_passant(origem, destino)
        else:  # Movimento normal
            peca.move(*destino)
            if isinstance(peca, Peao) and abs(destino[0] - origem[0]) == 2:
                self.__passant.append(peca)

        if isinstance(peca, Peao) and destino[0] in (0, 7):
            new = self.__promote(self.cor(origem))
            classe = {
                'Rainha': Rainha,
                'Bispo': Bispo,
                'Cavalo': Cavalo,
                'Torre': Torre,
            }
            self.tabuleiro.append(classe[new](*destino, self.cor(origem)))
            self.tabuleiro.remove(peca)

        if self.screen:
            if self.__is_check(self.vez):
                print("Cheque")
            if self.__is_mate(self.vez):
                print("Mate")

        self.vez = self.inv_cor(self.vez)
        return True

    def __move_roque(self, _id):
        x = 7 if _id[0] == 'B' else 0
        para = 1 if _id[1] == 'L' else -1
        torre = 7 if _id[1] == 'L' else 0

        self.casa([x, 3]).move(x, 3 + 2 * para)
        self.casa([x, torre]).move(x, 3 + para)

    def __comer_passant(self, origem, destino):
        comer = [origem[0], destino[1]]
        peca = self.casa(origem)
        outra = self.casa(comer)
        peca.move(*destino)
        self.tabuleiro.remove(outra)

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

    def __is_mate(self, _for):
        if not self.__is_check(_for):
            return False
        dic = {
            'P': self.pretas,
            'B': self.brancas,
        }

        on_check = self.inv_cor(_for)
        deffen = dic[on_check]
        for protect in deffen:
            for move in protect.possiveis(True):
                if self.__validate_move(protect.pos, move, on_check):
                    new = Xadrez(self.copy())
                    new.vez = on_check
                    new.__move(protect.pos, move)
                    if not new.__is_check(_for):
                        return False
                    del new
        return True

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

    # Pygame

    def blit(self, force=True):
        cor = 255
        for x in range(8):
            for y in range(8):
                if force:
                    self.__draw_rect(x, y, (cor, cor, cor))
                cor = 400 - cor
            cor = 400 - cor

        for peca in self.tabuleiro:
            img = self.imgs[peca.cor][peca.__class__.__name__]
            self.screen.blit(img, (peca.y * 100, peca.x * 100))

    def __text(self, text, color=(0, 0, 0)):
        img = pg.font.SysFont('Agency FB', 95, True).render(text, True, color)
        img_w, img_h = img.get_size()
        self.screen.blit(img, ((self.screen_size - img_w) // 2, (self.screen_size - img_h) // 2))
        pg.display.update()
        self.__wait_for_click()
        self.blit()

    def __mark(self, x, y):
        if self.__marked:
            self.blit()
        peca = self.casa([x, y])
        if peca is None:
            return
        self.__marked = [[x, y], []]
        self.__draw_rect(y, x, (100, 150, 250))

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
                val = val and self.__validate_not_check_move((x, y), (x1, y1))
            if val:
                if peca.cor != self.vez:
                    cor = (250, 250, 100)  # Amarelo
                elif val == 'roque':
                    cor = (200, 100, 250)  # Roxo
                elif comer:
                    cor = (250, 100, 150)  # Vermelho
                else:
                    cor = (100, 250, 150)  # Verde
                self.__draw_rect(y1, x1, cor)
                self.__marked[1].append((x1, y1))

    def __draw_rect(self, x, y, color):
        pg.draw.rect(self.screen, (0, 0, 0), ((x * 100, y * 100), (100, 100)))
        pg.draw.rect(self.screen, color, ((x * 100 + 1, y * 100 + 1), (98, 98)))

    def __wait_for_click(self):
        while self.running:
            for evt in pg.event.get():
                if evt.type == pg.QUIT:
                    self.running = False
                elif evt.type == pg.MOUSEBUTTONDOWN:
                    return evt.pos

    def __promote(self, color):
        self.screen.fill((255, 255, 255))
        pg.draw.rect(self.screen, (0, 0, 0), ((0, self.screen_size // 2 - 1), (self.screen_size, 2)))
        pg.draw.rect(self.screen, (0, 0, 0), ((self.screen_size // 2 - 1, 0), (2, self.screen_size)))
        possibs = ['Rainha', 'Cavalo', 'Bispo', 'Torre']
        for i, peca in enumerate(possibs):
            img = pg.transform.scale(self.imgs[color][peca], (self.screen_size // 8, self.screen_size // 8))
            self.screen.blit(img, (
                (i // 2) * (self.screen_size // 2) + 3 * self.screen_size // 16,
                (i % 2) * (self.screen_size // 2) + 3 * self.screen_size // 16))
        pg.display.update()
        try:
            x, y = self.__wait_for_click()
        except TypeError:
            return
        return possibs[(x * 2) // self.screen_size * 2 + (y * 2) // self.screen_size]

    def event_listener(self):
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                self.running = False
            elif evt.type == pg.MOUSEBUTTONDOWN:
                w = evt.pos[0] // 100
                h = evt.pos[1] // 100
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

    def loop(self):
        self.screen: pg.Surface = pg.display.set_mode((self.screen_size, self.screen_size))
        self.imgs = {
            'P': {name: pg.transform.scale(pg.image.load(f'./assets/Preto/{name}.png'), (100, 100))
                  for name in ['Peao', 'Bispo', 'Torre', 'Cavalo', 'Rei', 'Rainha']},
            'B': {name: pg.transform.scale(pg.image.load(f'./assets/Branco/{name}.png'), (100, 100))
                  for name in ['Peao', 'Bispo', 'Torre', 'Cavalo', 'Rei', 'Rainha']}
        }
        clock = Clock()

        self.blit()
        while self.running:
            self.blit(False)
            self.event_listener()
            pg.display.update()
            clock.tick(100)


if __name__ == '__main__':
    Xadrez().loop()
