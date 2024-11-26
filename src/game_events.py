from dataclasses import dataclass
from typing import List, Optional, Dict
from .deck import Card

@dataclass
class GameEvent:
    event_type: str  # 'deal', 'bet', 'fold', 'win', etc.
    player_name: Optional[str] = None
    amount: Optional[float] = None
    cards: Optional[List[Card]] = None
    pot: Optional[float] = None
    community_cards: Optional[List[Card]] = None
    player_stacks: Optional[Dict[str, float]] = None
    description: Optional[str] = None
