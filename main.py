from multipledispatch import dispatch
from copy import deepcopy
import pygame as pg
from time import sleep
Pecas = __import__('pecas')
pg.init()


class Tabuleiro:
    def __init__(self, tabuleiro):
        """
        Cria um tabuleiro com diversas características para realizar operações
        :param tabuleiro: Uma série de iteráveis de mesmo tamanho, que formam as linhas de um tabuleiro retângular.
        """
        self.__tabuleiro = list(tabuleiro)
        self.largura = len(self.__tabuleiro[0])
        for line in self.__tabuleiro:
            line = list(line)
            if len(line) != self.largura:
                raise ValueError('Todas as linhas devem ter o mesmo tamanho.')
        self.altura = len(self.__tabuleiro)
        self.casas = self.altura * self.largura

    def __repr__(self):
        return self.__tabuleiro

    def __str__(self):
        return '\n'.join([' '.join(line) for line in self.__tabuleiro])

    @property
    def tabuleiro(self):
        return self.__tabuleiro

    @property
    def bordas(self):
        bordas = dict()
        bordas['D'], bordas['U'] = self.__tabuleiro[-1:0].copy()
        bordas['R'], bordas['L'] = self.rot()[-1:0].copy()
        return bordas

    @dispatch(list)
    def casa(self, coordenada):
        """
        Retorna o valor da casa com linha e coluna informadas
        :param coordenada: Um iterável de tamanho 2, que representa o índice da linha e da coluna, respectivamente.
        :return: Valor da casa determinada
        """
        return self.__tabuleiro[coordenada[0]][coordenada[1]]

    @dispatch(int, int)
    def casa(self, x, y):
        """
        Retorna o valor da casa com linha e coluna informadas
        :param x: O índice da linha
        :param y: O índice da coluna
        :return: Valor da casa determinada
        """
        return self.__tabuleiro[x][y]

    @dispatch(list, object)
    def set_casa(self, coordenada, value):
        ret = self.casa(coordenada)
        self.__tabuleiro[coordenada[0]][coordenada[1]] = value
        return ret

    @dispatch(int, int, object)
    def set_casa(self, x, y, value):
        ret = self.casa(x, y)
        self.__tabuleiro[x][y] = value
        return ret

    def rot(self):
        return [[line[i] for line in self.__tabuleiro] for i in range(self.largura)[::-1]]

    def diag(self, offset=0, axis=1):
        if axis == 1:
            tab = self.tabuleiro
        elif axis == -1:
            tab = self.rot()
        else:
            raise ValueError("Axis deve ser 1 ou -1")
        x = max(0, -offset)
        y = max(0, offset)
        while True:
            try:
                yield tab[x][y]
            except IndexError:
                break
            else:
                x += 1
                y += 1
                if not (0 <= x < 8 and 0 <= y < 8):
                    break

    def encontra(self, value, todos=False):
        """
        Retorna a localização do valor informdao
        :param value: O valor que será buscado
        :param todos: Define se todas as ocorrências serão retornadas (True), ou se somente a primeira (False)
        :return: Retorna a primeira ou todas as ocorrências do determinado valor no formato de tupla: (linha, coluna)
        """

        def traduz(n):
            return n // self.largura, n % self.largura

        one_line = sum(self.__tabuleiro, [])
        inds = [one_line.index(value)]
        if todos:
            while value in one_line[inds[-1] + 1:]:
                inds.append(one_line.index(value, inds[-1] + 1))
            return [traduz(ind) for ind in inds]
        return traduz(inds[0])

    def linha(self, numero_da_linha: int):
        """
        :param numero_da_linha: O número da linha a ser retornada
        :return: A linha de número :numero_da_linha:
        """
        return self.__tabuleiro[numero_da_linha]

    def coluna(self, numero_da_coluna: int):
        """
        :param numero_da_coluna: O número da coluna a ser retornada
        :return: A coluna de número :numero_da_linha:
        """
        return self.rot()[7-numero_da_coluna]

    def troca_casas(self, casa_1, casa_2):
        """
        Inverte os valores nas duas casas informadas
        :param casa_1: Coordenada na forma: (linha, coluna) da primeira casa
        :param casa_2: Coordenada na forma: (linha, coluna) da segunda casa
        """
        v1 = self.casa(list(casa_1))
        v2 = self.set_casa(list(casa_2), v1)
        self.set_casa(list(casa_1), v2)
        return v1, v2


class Xadrez(Tabuleiro):
    def __init__(self, empty='XX', configuracao_inicial=None):
        if not empty:
            self.empty = 'XX'
        elif len(empty) == 1:
            self.empty = empty * 2
        else:
            self.empty = empty[:2]
        if configuracao_inicial is None:
            configuracao_inicial = self.__criar()
        super().__init__(configuracao_inicial)
        self.__comidas = {'B': [], 'P': []}
        self.vez = 'B'
        self.__roque = {
            'PL': True,
            'PC': True,
            'BL': True,
            'BC': True,
        }
        self.__passant = []
        self.__promote_counter = 0

        # Pygame
        self.running = True
        self.__previous = [['' for _ in range(8)] for _ in range(8)]
        self.__marked = None

        self.screen_size = 800
        self.screen: pg.Surface = pg.display.set_mode((self.screen_size, self.screen_size))
        self.imgs = {
            True: {name: pg.transform.scale(pg.image.load(f'./assets/Preto/{name}.png'), (100, 100))
                   for name in ['p', 'b', 't', 'c', 're', 'ra']},
            False: {name: pg.transform.scale(pg.image.load(f'./assets/Branco/{name}.png'), (100, 100))
                    for name in ['p', 'b', 't', 'c', 're', 'ra']}
        }

    def __criar(self):
        l1 = ['T1', 'C1', 'B1', 'RE', 'RA', 'B2', 'C2', 'T2']
        l2 = [f'P{x}' for x in range(1, 9)]
        l3a6 = [self.empty for _ in range(8)]
        l7 = [x.lower() for x in l2]
        l8 = [x.lower() for x in l1]
        return [l1, l2] + [l3a6.copy() for _ in range(4)] + [l7, l8]

    def __cor(self, casa):
        if self.casa(casa) == self.empty:
            return None
        return 'P' if self.casa(casa).isupper() else 'B'

    def __validate_move(self, origem, destino, _peca: str, vez, comer=False):
        classe = {
            'p': lambda a, b: Pecas.Peao(a, b, 1) if vez == 'P' else Pecas.Peao(a, b, -1),
            'b': Pecas.Bispo,
            't': Pecas.Torre,
            'c': Pecas.Cavalo,
            're': Pecas.Rei,
            'ra': Pecas.Rainha,
        }

        peca = _peca.lower().rstrip('+12345678')
        x1, y1 = origem
        x2, y2 = destino
        if peca == 'c':
            path = [self.empty]
        elif x1 == x2:
            beg = min(y1, y2)
            end = y1 + y2 - beg
            path = self.coluna(x1)[beg+1:end]
        elif y1 == y2:
            beg = min(x1, x2)
            end = x1 + x2 - beg
            path = self.linha(y1)[beg + 1:end]
        else:
            dx = x2 - x1
            dy = y2 - y1
            if dx == dy:
                offset = x1 - y1
                path = list(self.diag(offset))
                i1 = origem[0] - max(offset, 0)
                i2 = destino[0] - max(offset, 0)
            else:  # dx == -dy
                offset = x1 + y1 - 7
                path = list(self.diag(offset, -1))
                i1 = origem[1] - max(offset, 0)
                i2 = destino[1] - max(offset, 0)
            beg = min(i1, i2)
            end = i1 + i2 - beg
            path = path[beg+1:end]

        if len(set(path)) > 1 or (path and self.empty not in path) or self.__cor([y2, x2]) == vez:
            return False

        valido = classe[peca](y1, x1).validate(destino[::-1], comer)
        if valido and peca == 're':
            delta = x2 - x1
            if abs(delta) == 2:
                if _peca == 're':
                    if delta == 2 and self.__roque['BL']:
                        path = self.tabuleiro[7][4:7]
                    elif delta == -2 and self.__roque['BC']:
                        path = self.tabuleiro[7][1:3]
                    else:
                        return False
                    if len(set(path)) == 1 and path[0] == self.empty:
                        self.__roque['BL'] = False
                        self.__roque['BC'] = False
                        return 'roque'
                    return False
                elif _peca == 'RE':
                    if delta == 2 and self.__roque['PL']:
                        path = self.tabuleiro[0][4:7]
                    elif delta == -2 and self.__roque['PC']:
                        path = self.tabuleiro[0][1:3]
                    else:
                        return False
                    if len(set(path)) == 1 and path[0] == self.empty:
                        self.__roque['PL'] = False
                        self.__roque['PC'] = False
                        return 'roque'
                    return False

                return 'roque' if len(set(path)) == 1 and path[0] == self.empty else False

        return valido

    def __brancas(self):
        return [peca for peca in sum(self.tabuleiro, []) if peca.islower() and peca != self.empty]

    def __pretas(self):
        return [peca for peca in sum(self.tabuleiro, []) if peca.isupper() and peca != self.empty]

    def __text(self, text, color=(0, 0, 0)):
        img = pg.font.SysFont('Agency FB', 95, True).render(text, True, color)
        img_w, img_h = img.get_size()
        self.screen.blit(img, ((self.screen_size - img_w)//2, (self.screen_size - img_h)//2))
        pg.display.update()
        self.__wait_for_click()
        self.blit(True)

    def __move(self, origem, destino):
        self.__passant = []
        peca = self.casa(origem)
        comer = self.casa(destino)
        if self.__cor(origem) != self.vez:
            self.__text("Não é sua vez")
            return False

        if comer != self.empty:
            self.__comidas[self.vez].append(comer)
        if peca.lower() == 're' and abs(origem[1] - destino[1]) == 2:
            cor = self.__cor(origem)
            modo = 'L' if destino[1] > origem[1] else 'C'
            self.__move_roque(cor + modo)
        elif peca.lower()[0] == 'p' and abs(origem[1] - destino[1]) == 1 and comer == self.empty:
            self.__comer_passant(origem, destino)
        else:
            self.set_casa(origem, self.empty)
            self.set_casa(destino, peca)
            if peca.lower()[0] == 'p' and abs(destino[0] - origem[0]) == 2:
                self.__passant.append(peca)
        if peca in ('RE', 'T1'):
            self.__roque['PC'] = False
        if peca in ('RE', 'T2'):
            self.__roque['PL'] = False
        if peca in ('re', 't1'):
            self.__roque['BC'] = False
        if peca in ('re', 't2'):
            self.__roque['BL'] = False
        if peca.lower()[0] == 'p' and destino[0] in (0, 7):
            new = self.__promote(self.__cor(origem))
            self.__promote_counter += 1
            self.set_casa(destino, f'{new}+{self.__promote_counter}')

        self.vez = 'P' if self.vez == 'B' else 'B'
        return True

    def __move_roque(self, _id):
        if _id == 'BL':
            self.tabuleiro[7] = self.tabuleiro[7][:3] + [self.empty, 't2', 're', self.empty, self.empty]
        elif _id == 'BC':
            self.tabuleiro[7] = [self.empty, 're', 't1', self.empty] + self.tabuleiro[7][4:]
        elif _id == 'PL':
            self.tabuleiro[0] = self.tabuleiro[0][:3] + [self.empty, 'T2', 'RE', self.empty, self.empty]
        elif _id == 'PC':
            self.tabuleiro[0] = [self.empty, 'RE', 'T1', self.empty] + self.tabuleiro[0][4:]

    def __comer_passant(self, origem, destino):
        comer = [origem[0], destino[1]]
        self.set_casa(destino, self.casa(origem))
        self.set_casa(comer, self.empty)
        self.set_casa(origem, self.empty)

    @dispatch(str)
    def __is_check(self, turn):
        turn = turn.upper()
        other = 'RE' if turn == 'B' else 're'
        dic = {
            'P': self.__pretas,
            'B': self.__brancas,
        }
        king_pos = self.encontra(other)
        for peca in dic[turn]():
            if self.__validate_move(self.encontra(peca), king_pos, peca, self.vez, comer=True):
                return True
        return False

    @dispatch()
    def __is_check(self):
        if self.__is_check('P'):
            return 'P'
        elif self.__is_check('B'):
            return 'B'
        return False

    @dispatch(str)
    def __is_mate(self, turn):
        turn = turn.upper()
        if not self.__is_check(turn):
            return False
        other = 'RE' if turn == 'B' else 're'
        king_pos = self.encontra(other)
        possibs = Pecas.Rei(*king_pos).possiveis()
        for poss in possibs:
            if self.casa(list(poss)) == self.empty:
                new = deepcopy(self.tabuleiro)
                branch = Xadrez(configuracao_inicial=new)
                branch.troca_casas(king_pos, poss)
                if not branch.__is_check(turn):
                    return False
        return True

    @dispatch()
    def __is_mate(self):
        if self.__is_mate('P'):
            return 'P'
        elif self.__is_mate('B'):
            return 'B'
        return False

    def __validate_passant(self, origem, destino):
        comer = [destino[0], origem[1]]
        cor1 = self.__cor(origem[::-1])
        cor2 = self.__cor(comer[::-1])
        falsy = [
            not self.casa(origem[::-1]).lower().startswith('p'),
            not self.casa(comer[::-1]).lower().startswith('p'),
            cor1 == cor2,
            None in (cor1, cor2),
            self.casa(destino[::-1]) != self.empty,
            self.casa(comer[::-1]) not in self.__passant
        ]
        if any(falsy):
            return False
        return 'passant'

    # Pygame

    def blit(self, force=False):
        cor = 255
        for x in range(8):
            for y in range(8):
                if self.__previous[x][y] != self.tabuleiro[x][y] or force:
                    self.__draw_rect(x, y, (cor, cor, cor))
                cor = 400 - cor
            cor = 400 - cor

        for y, line in enumerate(self.tabuleiro):
            for x, peca in enumerate(line):
                if peca != self.empty:
                    img = self.imgs[peca.isupper()][peca.lower().rstrip('+12345678')]
                    self.screen.blit(img, (x*100, y*100))
        self.__previous = deepcopy(self.tabuleiro)

    def __mark(self, x, y):
        if self.__marked:
            self.blit(True)
        if self.casa(y, x) == self.empty:
            return
        self.__marked = [[y, x], []]
        self.__draw_rect(x, y, (100, 150, 250))

        classe = {
            'b': Pecas.Bispo,
            't': Pecas.Torre,
            'c': Pecas.Cavalo,
            're': Pecas.Rei,
            'ra': Pecas.Rainha,
        }

        _peca = self.casa(y, x)
        branca = _peca.islower()
        peca = _peca.lower().rstrip('+12345678')
        if peca == 'p':
            obj = Pecas.Peao(y, x, (0.5 - int(branca)) * 2)
        elif peca == self.empty:
            return
        else:
            obj = classe[peca](y, x)
        for y1, x1 in obj.possiveis(True):
            comer = self.casa(y1, x1) != self.empty
            cor_da_peca = 'B' if branca else 'P'
            if (x1 != x and peca == 'p' and (not comer) and y not in (3, 4)) or (x1 == x and peca == 'p' and comer):
                continue
            elif peca == 'p' and x1 != x and y in (3, 4) and not comer:
                val = self.__validate_passant([x, y], [x1, y1])
                comer = True
            else:
                val = self.__validate_move((x, y), (x1, y1), _peca, cor_da_peca, comer)
            if val:
                if cor_da_peca != self.vez:
                    cor = (250, 250, 100)  # Amarelo
                elif val == 'roque':
                    cor = (200, 100, 250)  # Roxo
                elif comer:
                    cor = (250, 100, 150)  # Vermelho
                else:
                    cor = (100, 250, 150)  # Verde
                self.__draw_rect(x1, y1, cor)
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
        possibs = ['ra', 'c', 'b', 't']
        for i, peca in enumerate(possibs):
            img = pg.transform.scale(self.imgs[color == 'P'][peca], (self.screen_size // 8, self.screen_size // 8))
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
                x = evt.pos[0] // 100
                y = evt.pos[1] // 100
                if self.__marked:
                    if (x, y) in self.__marked[1]:
                        ok = self.__move(self.__marked[0], [y, x])
                        if ok:
                            self.blit(True)
                        self.__marked = None
                    elif self.casa(y, x) != self.empty:
                        self.__mark(x, y)
                    else:
                        self.blit(True)
                        self.__marked = None
                else:
                    self.__mark(x, y)


# TODO:
# Mostar apenas movimentos que não colocam o Rei em cheque
# Mate


if __name__ == '__main__':
    this = Xadrez('-')
    while this.running:
        this.event_listener()
        this.blit()
        pg.display.update()
        sleep(0.1)
