from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import IntEnum
from collections import Counter
from .deck import Card, Rank, Suit
import random

class HandRank(IntEnum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

@dataclass
class HandStrength:
    rank: HandRank
    high_cards: List[int]  # Used for breaking ties

class Player:
    def __init__(self, name: str, stack: float = 1000.0):
        self.name = name
        self.stack = stack
        self.hole_cards: List[Card] = []
        self.current_bet = 0.0
        self.is_active = True
        self.position = "BTN"  # Default position
        self.position_index = -1  # Numerical position index
        self.folded = False
        self.num_players = 6

    def reset_hand(self):
        """Reset player's hand for a new round."""
        self.hole_cards = []
        self.current_bet = 0.0
        self.is_active = True
        self.folded = False
        # Don't reset position or stack here

    def receive_card(self, card: Card):
        """Receive a hole card."""
        self.hole_cards.append(card)

    def evaluate_hand(self, community_cards: List[Card]) -> HandStrength:
        """Evaluate the best possible hand using hole cards and community cards."""
        if not community_cards:
            # Pre-flop evaluation - much stricter
            ranks = [card.rank for card in self.hole_cards]
            suits = [card.suit for card in self.hole_cards]
            
            # Pocket pairs - only high pairs count as pairs
            if ranks[0] == ranks[1]:
                rank_value = list(Rank).index(ranks[0])
                if rank_value >= list(Rank).index(Rank.TEN):
                    return HandStrength(HandRank.PAIR, [rank_value])
                return HandStrength(HandRank.HIGH_CARD, [rank_value])
            
            # High cards - need at least one face card
            high_card = max(list(Rank).index(r) for r in ranks)
            if high_card >= list(Rank).index(Rank.JACK):
                return HandStrength(HandRank.HIGH_CARD, [high_card])
            return HandStrength(HandRank.HIGH_CARD, [0])  # Very weak hand

        # Post-flop evaluation
        all_cards = self.hole_cards + community_cards
        return self._evaluate_cards(all_cards)

    def _evaluate_cards(self, cards: List[Card]) -> HandStrength:
        """Evaluate the best possible 5-card hand from given cards - stricter requirements."""
        sorted_cards = sorted(cards, reverse=True)
        
        # Check for straight flush - require exact 5 cards
        if straight_flush := self._check_straight_flush(sorted_cards):
            if len(straight_flush) == 5:
                if straight_flush[0].rank == Rank.ACE:
                    return HandStrength(HandRank.ROYAL_FLUSH, [])
                return HandStrength(HandRank.STRAIGHT_FLUSH, [list(Rank).index(straight_flush[0].rank)])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for four of a kind - require exactly 4 cards
        if four_kind := self._check_four_of_a_kind(sorted_cards):
            if len(four_kind) == 4:
                return HandStrength(HandRank.FOUR_OF_A_KIND, [list(Rank).index(four_kind[0].rank)])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for full house - require exactly 5 cards
        if full_house := self._check_full_house(sorted_cards):
            if len(full_house) == 5:
                return HandStrength(HandRank.FULL_HOUSE, [list(Rank).index(full_house[0].rank)])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for flush - require exactly 5 cards of the same suit
        if flush := self._check_flush(sorted_cards):
            if len(flush) == 5:
                return HandStrength(HandRank.FLUSH, [list(Rank).index(c.rank) for c in flush[:5]])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for straight - require exactly 5 consecutive cards
        if straight := self._check_straight(sorted_cards):
            if len(straight) == 5:
                return HandStrength(HandRank.STRAIGHT, [list(Rank).index(straight[0].rank)])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for three of a kind - require exactly 3 cards
        if three_kind := self._check_three_of_a_kind(sorted_cards):
            if len(three_kind) == 3:
                return HandStrength(HandRank.THREE_OF_A_KIND, [list(Rank).index(three_kind[0].rank)])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for two pair - require exactly 4 cards (2+2)
        if two_pair := self._check_two_pair(sorted_cards):
            if len(two_pair) == 4:
                return HandStrength(HandRank.TWO_PAIR, [list(Rank).index(c.rank) for c in two_pair[:4]])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # Check for pair - require exactly 2 cards
        if pair := self._check_pair(sorted_cards):
            if len(pair) == 2:
                return HandStrength(HandRank.PAIR, [list(Rank).index(c.rank) for c in pair[:2]])
            return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])
        
        # High card
        return HandStrength(HandRank.HIGH_CARD, [list(Rank).index(c.rank) for c in sorted_cards[:5]])

    def _check_royal_flush(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for royal flush."""
        for suit in Suit:
            suited_cards = [card for card in cards if card.suit == suit]
            if len(suited_cards) >= 5:
                royal_cards = [card for card in suited_cards 
                             if card.rank in [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN]]
                if len(royal_cards) == 5:
                    return royal_cards
        return None

    def _check_straight_flush(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for straight flush."""
        for suit in Suit:
            suited_cards = sorted([card for card in cards if card.suit == suit],
                                key=lambda x: list(Rank).index(x.rank))
            if straight := self._check_straight(suited_cards):
                return straight
        return None

    def _check_four_of_a_kind(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for four of a kind."""
        rank_counts = Counter(card.rank for card in cards)
        for rank, count in rank_counts.items():
            if count == 4:
                four_cards = [card for card in cards if card.rank == rank]
                kicker = next(card for card in cards if card.rank != rank)
                return four_cards + [kicker]
        return None

    def _check_full_house(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for full house."""
        rank_counts = Counter(card.rank for card in cards)
        three_rank = None
        pair_rank = None
        
        for rank, count in rank_counts.items():
            if count >= 3 and three_rank is None:
                three_rank = rank
            elif count >= 2 and pair_rank is None:
                pair_rank = rank
                
        if three_rank and pair_rank:
            three_cards = [card for card in cards if card.rank == three_rank][:3]
            pair_cards = [card for card in cards if card.rank == pair_rank][:2]
            return three_cards + pair_cards
        return None

    def _check_flush(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for flush."""
        for suit in Suit:
            suited_cards = [card for card in cards if card.suit == suit]
            if len(suited_cards) >= 5:
                return suited_cards[:5]
        return None

    def _check_straight(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for straight."""
        ranks = sorted(set(card.rank for card in cards), 
                      key=lambda x: list(Rank).index(x))
        
        # Check for Ace-low straight
        if (Rank.ACE in ranks and 
            Rank.TWO in ranks and 
            Rank.THREE in ranks and 
            Rank.FOUR in ranks and 
            Rank.FIVE in ranks):
            return sorted([card for card in cards 
                         if card.rank in [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE]])
        
        # Check for regular straights
        for i in range(len(ranks) - 4):
            if all(list(Rank).index(ranks[i+j+1]) - list(Rank).index(ranks[i+j]) == 1 
                   for j in range(4)):
                straight_ranks = ranks[i:i+5]
                return sorted([card for card in cards if card.rank in straight_ranks])[:5]
        return None

    def _check_three_of_a_kind(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for three of a kind."""
        rank_counts = Counter(card.rank for card in cards)
        for rank, count in rank_counts.items():
            if count >= 3:
                three_cards = [card for card in cards if card.rank == rank][:3]
                other_cards = [card for card in cards if card.rank != rank][:2]
                return three_cards + other_cards
        return None

    def _check_two_pair(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for two pair."""
        rank_counts = Counter(card.rank for card in cards)
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]
        if len(pairs) >= 2:
            pair1_cards = [card for card in cards if card.rank == pairs[0]][:2]
            pair2_cards = [card for card in cards if card.rank == pairs[1]][:2]
            kicker = next(card for card in cards 
                         if card.rank != pairs[0] and card.rank != pairs[1])
            return pair1_cards + pair2_cards + [kicker]
        return None

    def _check_pair(self, cards: List[Card]) -> Optional[List[Card]]:
        """Check for pair."""
        rank_counts = Counter(card.rank for card in cards)
        for rank, count in rank_counts.items():
            if count >= 2:
                pair_cards = [card for card in cards if card.rank == rank][:2]
                other_cards = [card for card in cards if card.rank != rank][:3]
                return pair_cards + other_cards
        return None

    def make_decision(self, to_call: float, pot: float, community_cards: List[Card] = None) -> Tuple[str, float]:
        """Make a decision based on current game state."""
        if to_call > self.stack:
            return "fold", 0.0

        # Get hand strength
        hand_strength = self.evaluate_hand(community_cards)
        
        # Basic position-based strategy
        position_ranks = {
            "BTN": 5,  # Button (last to act)
            "CO": 4,   # Cut-off
            "MP": 3,   # Middle position
            "UTG": 2,  # Under the gun
            "BB": 1,   # Big blind
            "SB": 0    # Small blind
        }
        position_strength = position_ranks.get(self.position, 0)
        is_late_position = position_strength >= 4

        # Pre-flop strategy
        if not community_cards:
            return self._preflop_strategy(to_call, pot, is_late_position)
        
        # Post-flop strategy based on hand strength and position
        return self._postflop_strategy(hand_strength, to_call, pot, is_late_position)

    def _preflop_strategy(self, to_call: float, pot: float, is_late_position: bool) -> Tuple[str, float]:
        """Preflop decision making strategy."""
        # Check if we have pocket pairs
        has_pair = len(self.hole_cards) == 2 and self.hole_cards[0].rank == self.hole_cards[1].rank
        
        # Check if we have high cards (A, K, Q)
        high_ranks = {Rank.ACE, Rank.KING, Rank.QUEEN}
        high_cards = [card for card in self.hole_cards if card.rank in high_ranks]
        
        # Basic strategy
        if has_pair:
            # More aggressive with pairs
            if to_call == 0:
                return "raise", min(pot * 0.75, self.stack)
            elif to_call <= self.stack * 0.1:
                return "call", to_call
            else:
                return "fold", 0.0
        elif len(high_cards) >= 1:
            # Play high cards more aggressively in late position
            if is_late_position:
                if to_call == 0:
                    return "raise", min(pot * 0.5, self.stack)
                elif to_call <= self.stack * 0.05:
                    return "call", to_call
            return "fold", 0.0
        else:
            # Fold weak hands
            if to_call == 0:
                return "call", 0.0
            return "fold", 0.0

    def _postflop_strategy(self, hand_strength: HandStrength, to_call: float, pot: float, is_late_position: bool) -> Tuple[str, float]:
        """Postflop decision making strategy."""
        # More aggressive with strong hands
        if hand_strength.rank >= HandRank.THREE_OF_A_KIND:
            if to_call == 0:
                return "raise", min(pot, self.stack)
            elif to_call <= self.stack * 0.3:
                return "call", to_call
            else:
                return "fold", 0.0
        
        # Play draws and pairs more aggressively in late position
        elif hand_strength.rank >= HandRank.PAIR and is_late_position:
            if to_call == 0:
                return "raise", min(pot * 0.5, self.stack)
            elif to_call <= self.stack * 0.1:
                return "call", to_call
            else:
                return "fold", 0.0
        
        # Play conservatively with weak hands
        else:
            if to_call == 0:
                return "call", 0.0
            elif to_call <= self.stack * 0.05:
                return "call", to_call
            else:
                return "fold", 0.0
