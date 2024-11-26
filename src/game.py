from typing import List, Dict, Optional, Tuple, Callable
from src.deck import Deck, Card
from src.player import Player, HandStrength
from src.game_events import GameEvent
import random
from collections import defaultdict
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
import json
import os

@dataclass
class GameStatistics:
    hands_played: int = 0
    hands_won: int = 0
    total_profit: float = 0.0
    best_hand: Optional[HandStrength] = None
    all_in_count: int = 0
    fold_count: int = 0
    call_count: int = 0
    raise_count: int = 0

class PokerGame:
    def __init__(self, num_players: int = 6, initial_stack: float = 1000.0,
                 small_blind: float = 5.0, big_blind: float = 10.0,
                 four_card_flop: bool = False):
        self.num_players = num_players
        self.initial_stack = initial_stack
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.four_card_flop = four_card_flop
        self.deck = Deck()
        self.players = [Player(f"Player {i+1}", initial_stack) for i in range(num_players)]
        self.community_cards: List[Card] = []
        self.pot = 0.0
        self.current_bet = 0.0
        self.button_pos = 0
        self.stats: Dict[str, GameStatistics] = defaultdict(GameStatistics)
        self.console = Console()
        self.event_callback: Optional[Callable[[GameEvent], None]] = None

    def set_event_callback(self, callback: Callable[[GameEvent], None]):
        """Set a callback function to receive game events."""
        self.event_callback = callback

    def _emit_event(self, event: GameEvent):
        """Emit a game event to the registered callback."""
        if self.event_callback:
            self.event_callback(event)

    def reset_hand(self):
        """Reset the game state for a new hand."""
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0.0
        self.current_bet = 0.0
        # Move button position
        self.button_pos = (self.button_pos + 1) % self.num_players
        
        # Update player positions relative to the button
        position_names = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        for i in range(self.num_players):
            pos = (i - self.button_pos) % self.num_players
            if pos < len(position_names):
                self.players[i].position = position_names[pos]
            else:
                # For tables larger than 6 players, use MP2, MP3, etc.
                self.players[i].position = f"MP{pos - 4}"  # MP2, MP3, etc.
        
        # Reset players but preserve their stacks
        for player in self.players:
            player.reset_hand()
            if player.stack <= 0:  # If player is bust, give them a new stack
                player.stack = self.initial_stack
                self._emit_event(GameEvent(
                    event_type="stack_reset",
                    player_name=player.name,
                    description=f"{player.name} was reset with new stack of ${self.initial_stack:.2f}",
                    amount=self.initial_stack
                ))

    def deal_hole_cards(self):
        """Deal two hole cards to each active player."""
        self.deck.shuffle()
        for _ in range(2):
            for player in self.players:
                if player.is_active:
                    card = self.deck.draw()
                    if card:
                        player.receive_card(card)

    def deal_flop(self):
        """Deal the flop cards."""
        num_flop_cards = 4 if self.four_card_flop else 3
        for _ in range(num_flop_cards):
            card = self.deck.draw()
            if card:
                self.community_cards.append(card)

    def deal_turn(self):
        """Deal the turn card."""
        card = self.deck.draw()
        if card:
            self.community_cards.append(card)

    def deal_river(self):
        """Deal the river card."""
        card = self.deck.draw()
        if card:
            self.community_cards.append(card)

    def _betting_round(self) -> bool:
        """Execute a betting round. Returns True if the round should continue."""
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) <= 1:
            return False

        start_pos = (self.button_pos + 3) % self.num_players  # Start after BB
        current_pos = start_pos

        while True:
            # Find next active player
            while not self.players[current_pos].is_active:
                current_pos = (current_pos + 1) % self.num_players

            player = self.players[current_pos]
            
            # Get player action
            action, amount = player.make_decision(
                self.current_bet - player.current_bet,
                self.pot,
                self.community_cards
            )

            # Process action
            if action == "fold":
                player.is_active = False
                self.stats[player.name].fold_count += 1
                self._emit_event(GameEvent(
                    event_type="fold",
                    player_name=player.name,
                    description=f"{player.name} folds"
                ))
            elif action == "call":
                call_amount = self.current_bet - player.current_bet
                player.stack -= call_amount
                player.current_bet = self.current_bet
                self.pot += call_amount
                self.stats[player.name].call_count += 1
                self._emit_event(GameEvent(
                    event_type="call",
                    player_name=player.name,
                    amount=call_amount,
                    pot=self.pot,
                    description=f"{player.name} calls ${call_amount:.2f}"
                ))
            elif action == "raise":
                raise_amount = amount - player.current_bet
                player.stack -= raise_amount
                player.current_bet = amount
                self.pot += raise_amount
                self.current_bet = amount
                self.stats[player.name].raise_count += 1
                self._emit_event(GameEvent(
                    event_type="raise",
                    player_name=player.name,
                    amount=raise_amount,
                    pot=self.pot,
                    description=f"{player.name} raises to ${amount:.2f}"
                ))

            # Check if round is complete
            active_players = [p for p in self.players if p.is_active]
            if len(active_players) <= 1:
                return False

            all_called = all(not p.is_active or p.current_bet == self.current_bet 
                           for p in self.players)
            if all_called and current_pos == start_pos:
                return True

            current_pos = (current_pos + 1) % self.num_players

    def play_hand(self) -> List[Tuple[Player, float]]:
        """Play a complete hand and return the winners with their winnings."""
        # Reset for new hand
        self.reset_hand()
        
        # Post blinds
        sb_pos = (self.button_pos + 1) % self.num_players
        bb_pos = (self.button_pos + 2) % self.num_players
        
        # Small blind
        self.players[sb_pos].stack -= self.small_blind
        self.players[sb_pos].current_bet = self.small_blind
        self.pot += self.small_blind
        self._emit_event(GameEvent(
            event_type="small_blind",
            player_name=self.players[sb_pos].name,
            amount=self.small_blind,
            pot=self.pot,
            description=f"{self.players[sb_pos].name} posts small blind: ${self.small_blind:.2f}"
        ))
        
        # Big blind
        self.players[bb_pos].stack -= self.big_blind
        self.players[bb_pos].current_bet = self.big_blind
        self.pot += self.big_blind
        self.current_bet = self.big_blind
        self._emit_event(GameEvent(
            event_type="big_blind",
            player_name=self.players[bb_pos].name,
            amount=self.big_blind,
            pot=self.pot,
            description=f"{self.players[bb_pos].name} posts big blind: ${self.big_blind:.2f}"
        ))

        # Deal hole cards
        self.deal_hole_cards()
        for player in self.players:
            self._emit_event(GameEvent(
                event_type="deal",
                player_name=player.name,
                cards=player.hole_cards,
                description=f"{player.name} receives hole cards"
            ))

        # Pre-flop betting
        if not self._betting_round():
            winners = self._resolve_winners()
            self._emit_event(GameEvent(
                event_type="hand_complete",
                description="Hand complete (pre-flop)"
            ))
            return winners

        # Flop
        self.deal_flop()
        self._emit_event(GameEvent(
            event_type="community",
            cards=self.community_cards[:3],
            community_cards=self.community_cards,
            description="Flop dealt"
        ))
        if not self._betting_round():
            winners = self._resolve_winners()
            self._emit_event(GameEvent(
                event_type="hand_complete",
                description="Hand complete (post-flop)"
            ))
            return winners

        # Turn
        self.deal_turn()
        self._emit_event(GameEvent(
            event_type="community",
            cards=[self.community_cards[3]],
            community_cards=self.community_cards,
            description="Turn dealt"
        ))
        if not self._betting_round():
            winners = self._resolve_winners()
            self._emit_event(GameEvent(
                event_type="hand_complete",
                description="Hand complete (post-turn)"
            ))
            return winners

        # River
        self.deal_river()
        self._emit_event(GameEvent(
            event_type="community",
            cards=[self.community_cards[4]],
            community_cards=self.community_cards,
            description="River dealt"
        ))
        if not self._betting_round():
            winners = self._resolve_winners()
            self._emit_event(GameEvent(
                event_type="hand_complete",
                description="Hand complete (post-river)"
            ))
            return winners

        winners = self._resolve_winners()
        self._emit_event(GameEvent(
            event_type="hand_complete",
            description="Hand complete (showdown)"
        ))
        return winners

    def _resolve_winners(self) -> List[Tuple[Player, float]]:
        """Determine the winner(s) of the hand and return them with their winnings."""
        active_players = [p for p in self.players if p.is_active]
        
        if len(active_players) == 0:
            # Edge case: all players folded (shouldn't happen, but handle it)
            return []
        
        if len(active_players) == 1:
            # Single winner (everyone else folded)
            winner = active_players[0]
            winnings = self.pot
            winner.stack += winnings
            self.stats[winner.name].hands_won += 1
            self.stats[winner.name].total_profit += winnings
            
            self._emit_event(GameEvent(
                event_type="win",
                player_name=winner.name,
                amount=winnings,
                description=f"{winner.name} wins ${winnings:.2f} (others folded)"
            ))
            
            return [(winner, winnings)]
        
        # Compare hands of all active players
        player_hands = []
        for player in active_players:
            hand_strength = player.evaluate_hand(self.community_cards)
            player_hands.append((player, hand_strength))
            
            # Update best hand if this is better
            if (not self.stats[player.name].best_hand or 
                hand_strength.rank.value > self.stats[player.name].best_hand.rank.value):
                self.stats[player.name].best_hand = hand_strength
        
        # Sort by hand strength (highest first)
        player_hands.sort(key=lambda x: (x[1].rank.value, x[1].high_cards), reverse=True)
        
        # Find all players with the best hand (could be multiple)
        best_hand_rank = player_hands[0][1].rank.value
        best_high_cards = player_hands[0][1].high_cards
        winners = []
        
        for player, hand in player_hands:
            if hand.rank.value == best_hand_rank and hand.high_cards == best_high_cards:
                winners.append(player)
            else:
                break
        
        # Split pot among winners
        winnings_per_player = self.pot / len(winners)
        results = []
        
        for winner in winners:
            winner.stack += winnings_per_player
            self.stats[winner.name].hands_won += 1
            self.stats[winner.name].total_profit += winnings_per_player
            results.append((winner, winnings_per_player))
            
            self._emit_event(GameEvent(
                event_type="win",
                player_name=winner.name,
                amount=winnings_per_player,
                description=f"{winner.name} wins ${winnings_per_player:.2f} with {winner.evaluate_hand(self.community_cards).rank.name}"
            ))
        
        return results

    def _log_hand_results(self, winners: List[Tuple[Player, float]], output_file: str):
        """Log the results of a hand to a file."""
        result = {
            "community_cards": [str(card) for card in self.community_cards],
            "pot_size": self.pot,
            "winners": [{
                "player": winner[0].name,
                "winnings": winner[1],
                "hole_cards": [str(card) for card in winner[0].hole_cards]
            } for winner in winners],
            "players": [{
                "name": player.name,
                "hole_cards": [str(card) for card in player.hole_cards],
                "stack": player.stack,
                "folded": player.folded,
                "is_active": player.is_active
            } for player in self.players]
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "a") as f:
            json.dump(result, f)
            f.write("\n")

    def run_simulation(self, num_hands: int, output_file: str):
        """Run the poker simulation for a specified number of hands."""
        for _ in range(num_hands):
            # Update hand statistics
            for player in self.players:
                self.stats[player.name].hands_played += 1

            # Rotate button position
            self.button_pos = (self.button_pos + 1) % self.num_players
            
            # Set player positions
            for i in range(self.num_players):
                pos = (i - self.button_pos) % self.num_players
                position_names = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
                self.players[i].position = position_names[pos]

            # Play the hand
            winners = self.play_hand()

            # Log the results
            self._log_hand_results(winners, output_file)

    def print_statistics(self):
        """Print the final statistics of the simulation."""
        table = Table(title="Poker Simulation Statistics")
        
        # Add columns
        table.add_column("Player", justify="right", style="cyan")
        table.add_column("Hands Won", justify="right")
        table.add_column("Win Rate", justify="right")
        table.add_column("Total Profit", justify="right")
        table.add_column("Best Hand", justify="left")
        table.add_column("All-ins", justify="right")
        table.add_column("Folds", justify="right")
        table.add_column("Calls", justify="right")
        table.add_column("Raises", justify="right")

        # Add rows
        for player in self.players:
            stats = self.stats[player.name]
            win_rate = (stats.hands_won / stats.hands_played * 100 
                       if stats.hands_played > 0 else 0)
            best_hand = (str(stats.best_hand.rank.name) 
                        if stats.best_hand else "None")
            
            table.add_row(
                player.name,
                str(stats.hands_won),
                f"{win_rate:.1f}%",
                f"${stats.total_profit:.2f}",
                best_hand,
                str(stats.all_in_count),
                str(stats.fold_count),
                str(stats.call_count),
                str(stats.raise_count)
            )

        self.console.print(table)
