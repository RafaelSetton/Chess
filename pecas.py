class Peca:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def validate(self, destino, comer=False):
        return tuple(destino) in self.possiveis(comer)

    def possiveis(self, comer=False):
        raise NotImplementedError


class Peao(Peca):
    def __init__(self, x, y, orientacao):
        super().__init__(x, y)
        self.orien = int(orientacao)
        self.line = 1 if self.orien == 1 else 6

    def possiveis(self, comer=False):
        res = [(self.x + self.orien, self.y + 1), (self.x + self.orien, self.y - 1)] if comer else []
        if self.x == self.line:
            res += [(self.x + self.orien*2, self.y), (self.x + self.orien, self.y)]
        else:
            res += [(self.x + self.orien, self.y)] if 0 <= self.x + self.orien < 8 else []
        return [coord for coord in res if 0 <= coord[0] < 8 and 0 <= coord[1] < 8]


class Torre(Peca):
    def possiveis(self, comer=False):
        return [(self.x, y) for y in range(8) if y != self.y] + [(x, self.y) for x in range(8) if x != self.x]


class Bispo(Peca):
    def possiveis(self, comer=False):
        res = [(self.x + delta, self.y + delta) for delta in range(-8, 8)] + \
              [(self.x + delta, self.y - delta) for delta in range(-8, 8)]
        return [(x, y) for x, y in res if 0 <= x < 8 and 0 <= y < 8 and x != self.x and y != self.y]


class Cavalo(Peca):
    def possiveis(self, comer=False):
        res = [(self.x + d1, self.y + d2) for d1 in (-2, -1, 1, 2) for d2 in (-2, -1, 1, 2) if abs(d1) + abs(d2) == 3]
        return [(x, y) for x, y in res if 0 <= x < 8 and 0 <= y < 8]


class Rei(Peca):
    def possiveis(self, comer=False):
        res = [(self.x + x, self.y + y) for x in (-1, 0, 1) for y in (-1, 0, 1) if (x, y) != (0, 0)]
        return [(x, y) for x, y in res if 0 <= x < 8 and 0 <= y < 8] + [(self.x, self.y - 2), (self.x, self.y + 2)]


class Rainha(Peca):
    def possiveis(self, comer=False):
        return Torre(self.x, self.y).possiveis() + Bispo(self.x, self.y).possiveis()
