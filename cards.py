import random

# Bakerbot-specific implementation of cards and hands.
# Card rankings come in the form of integers, ranging from 2-14.
# These represent the rankings of 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K and A.
# Suits are integers, ranging from 1-4: the Clubs, Diamonds, Hearts and Spades.

class Blackjack:
    def __init__(self):
        self.dealer = []
        self.player = []

    def gethandvalue(self, hand):
        normalised = [Card(10, 1) if card == Card(11, 1) or card == Card(12, 1) or card == Card(13, 1) else card for card in hand]
        aces = len([card for card in hand if card == Card(14, 1)])
        value = sum(normalised, aces * -14)

        while aces > 0 and value + 11 <= 21:
            value += 11
            aces -= 1

        value += aces
        return value

class Card:
    def __init__(self, rank, suit):
        if rank < 2 or rank > 14: raise ValueError("Rank too high/low!")
        if suit < 1 or suit > 4: raise ValueError("Suit too high/low!")

        self.printsuits = True
        self.cmpsuits = False
        self.rank = rank
        self.suit = suit

    def __gt__(self, other):
        if self.rank > other.rank: return True
        elif self.cmpsuits and self.suit > other.suit: return True
        else: return False

    def __ge__(self, other):
        if self.rank >= other.rank: return True
        elif self.cmpsuits and self.suit >= other.suit: return True
        else: return False

    def __lt__(self, other):
        if self.rank < other.rank: return True
        elif self.cmpsuits and self.suit < other.suit: return True
        else: return False

    def __le__(self, other):
        if self.rank <= other.rank: return True
        elif self.cmpsuits and self.suit <= other.suit: return True
        else: return False

    def __eq__(self, other):
        if self.cmpsuits and self.rank == other.rank and self.suit == other.suit: return True
        elif self.rank == other.rank: return True
        else: return False

    def __ne__(self, other):
        if self.cmpsuits and self.suit != other.suit: return True
        elif self.rank != other.rank: return True
        else: return False

    def __radd__(self, other):
        return other + self.rank

    def __suitstr__(self):
        if self.suit == 1: return "C"
        elif self.suit == 2: return "D"
        elif self.suit == 3: return "H"
        elif self.suit == 4: return "S"

    def __rankstr__(self):
        if self.rank >= 2 and self.rank <= 10: return str(self.rank)
        elif self.rank == 11: return "J"
        elif self.rank == 12: return "Q"
        elif self.rank == 13: return "K"
        elif self.rank == 14: return "A"

    def __repr__(self):
        if self.printsuits: return self.__rankstr__() + self.__suitstr__()
        else: return self.__rankstr__()

    def __str__(self):
        if self.printsuits: return self.__rankstr__() + self.__suitstr__()
        else: return self.__rankstr__()

    @classmethod
    def random(self):
        return Card(random.randint(2, 14), random.randint(1, 4))

    def setaction(self, action, boolean):
        if action == "print": self.printsuits = boolean
        elif action == "compare": self.cmpsuits = boolean
        else: raise ValueError("Incorrect action!")
