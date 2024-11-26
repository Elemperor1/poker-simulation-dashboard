from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Set, Optional
import random

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

    def __lt__(self, other):
        return list(Rank).index(self) < list(Rank).index(other)

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __lt__(self, other):
        return list(Rank).index(self.rank) < list(Rank).index(other.rank)

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"

class Deck:
    def __init__(self, seed: Optional[int] = None):
        self.cards: List[Card] = []
        self.discarded: Set[Card] = set()
        self._create_deck()
        if seed is not None:
            random.seed(seed)

    def _create_deck(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.discarded.clear()

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        """Draw a card from the deck."""
        if not self.cards:
            return None
        card = self.cards.pop()
        self.discarded.add(card)
        return card

    def reset(self):
        """Reset the deck to its initial state."""
        self._create_deck()
        self.shuffle()

    def remaining(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self.cards)

    def deal_specific_card(self, rank: Rank, suit: Suit) -> Optional[Card]:
        """Deal a specific card from the deck if available."""
        card = Card(rank, suit)
        try:
            self.cards.remove(card)
            self.discarded.add(card)
            return card
        except ValueError:
            return None
