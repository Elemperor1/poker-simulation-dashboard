import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.game import PokerGame
from src.game_events import GameEvent
from enum import Enum
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import deque, defaultdict
import time
import os

class GameVariant(Enum):
    THREE_CARD = False
    FOUR_CARD = True

class PokerApp:
    def __init__(self):
        self.game = PokerGame(num_players=6)  # Initialize with default values
        if 'game_events' not in st.session_state:
            st.session_state.game_events = deque(maxlen=100)  # Keep last 100 events
        if 'current_hand' not in st.session_state:
            st.session_state.current_hand = 1
        if 'needs_rerun' not in st.session_state:
            st.session_state.needs_rerun = False
        if 'player_profits' not in st.session_state:
            st.session_state.player_profits = defaultdict(lambda: defaultdict(float))
        if 'action_counts' not in st.session_state:
            st.session_state.action_counts = defaultdict(lambda: defaultdict(int))

    def _handle_game_event(self, event: GameEvent):
        """Handle incoming game events and update the UI."""
        st.session_state.game_events.append(event)
        
        # Track player actions
        if event.event_type in ['fold', 'call', 'raise']:
            st.session_state.action_counts[event.player_name][event.event_type] += 1
            if event.amount is not None:  # Track money put into pot
                st.session_state.player_profits[event.player_name][st.session_state.current_hand] -= event.amount
        
        # Track wins
        elif event.event_type == 'win':
            st.session_state.player_profits[event.player_name][st.session_state.current_hand] += event.amount
        
        # Track blinds
        elif event.event_type in ['small_blind', 'big_blind']:
            st.session_state.player_profits[event.player_name][st.session_state.current_hand] -= event.amount
        
        # Increment hand number when a hand is complete
        elif event.event_type == 'hand_complete':
            st.session_state.current_hand += 1
        
        st.session_state.needs_rerun = True

    def _create_profit_chart(self):
        """Create a line chart showing player profits over time."""
        df_data = []
        for player, hand_profits in st.session_state.player_profits.items():
            cumulative_profit = 0
            for hand in range(1, st.session_state.current_hand + 1):
                cumulative_profit += hand_profits[hand]
                df_data.append({
                    'Player': player,
                    'Hand': hand,
                    'Cumulative Profit': cumulative_profit
                })
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            # Add a zero line for reference
            fig = px.line(df, x='Hand', y='Cumulative Profit', color='Player',
                         title='Player Profits Over Time')
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Format y-axis to show dollar signs
            fig.update_layout(
                yaxis_title="Cumulative Profit ($)",
                yaxis_tickprefix="$"
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def _create_action_distribution(self):
        """Create a stacked bar chart showing player action distributions."""
        df_data = []
        for player, actions in st.session_state.action_counts.items():
            total_actions = sum(actions.values())
            if total_actions > 0:
                for action, count in actions.items():
                    df_data.append({
                        'Player': player,
                        'Action': action.capitalize(),
                        'Percentage': (count / total_actions) * 100
                    })
        
        if df_data:
            df = pd.DataFrame(df_data)
            fig = px.bar(df, x='Player', y='Percentage', color='Action',
                        title='Player Action Distribution', 
                        labels={'Percentage': 'Action %'})
            st.plotly_chart(fig, use_container_width=True)

    def render(self):
        """Render the Streamlit application."""
        st.set_page_config(page_title="Poker Simulation Dashboard", layout="wide")
        
        st.title("Poker Game Simulation")
        
        # Sidebar controls
        with st.sidebar:
            st.header("Game Controls")
            num_players = st.slider("Number of Players", 2, 9, 6)
            initial_stack = st.number_input("Initial Stack", 100.0, 10000.0, 1000.0)
            small_blind = st.number_input("Small Blind", 1.0, 100.0, 5.0)
            big_blind = st.number_input("Big Blind", 2.0, 200.0, 10.0)
            
            if st.button("Start New Game"):
                self.game = PokerGame(
                    num_players=num_players,
                    initial_stack=initial_stack,
                    small_blind=small_blind,
                    big_blind=big_blind
                )
                st.session_state.game_events.clear()
                st.session_state.current_hand = 1
                st.session_state.player_profits.clear()
                st.session_state.action_counts.clear()
                st.session_state.needs_rerun = True
                st.rerun()
        
        # Main content area
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.header("Game Statistics")
            
            # Player stacks table
            st.subheader("Current Player Stacks")
            stack_data = [{
                'Player': player.name,
                'Position': player.position,
                'Stack': f"${player.stack:.2f}",
                'Current Bet': f"${player.current_bet:.2f}",
                'Status': 'Folded' if player.folded else 'Active' if player.is_active else 'Not Active'
            } for player in self.game.players]
            st.dataframe(pd.DataFrame(stack_data), hide_index=True)
            
            # Profit chart
            self._create_profit_chart()
            
            # Action distribution
            self._create_action_distribution()
        
        with col2:
            st.header("Game Controls & Events")
            
            # Add number of hands to play
            num_hands = st.number_input("Number of Hands to Play", 1, 100, 1)
            
            if st.button("Play Hands", use_container_width=True):
                for _ in range(num_hands):
                    self.game.set_event_callback(self._handle_game_event)
                    winners = self.game.play_hand()
                    
                    # Display winners in a table
                    st.subheader(f"Hand {st.session_state.current_hand} Results")
                    winners_data = [{
                        'Player': winner.name,
                        'Amount Won': f"${amount:.2f}"
                    } for winner, amount in winners]
                    st.table(pd.DataFrame(winners_data))
            
            # Recent events table
            st.subheader("Recent Events")
            if st.session_state.game_events:
                events_data = [{
                    'Hand': st.session_state.current_hand,
                    'Event': event.description,
                    'Type': event.event_type.capitalize()
                } for event in list(st.session_state.game_events)[-10:]]  # Show last 10 events
                st.dataframe(pd.DataFrame(events_data), hide_index=True)

        # Handle rerun at the end of render
        if st.session_state.needs_rerun:
            st.session_state.needs_rerun = False
            time.sleep(0.1)
            st.rerun()

    def run_simulation(self, num_hands: int) -> Dict[str, Any]:
        """Run simulation and return statistics."""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        output_file = os.path.join(logs_dir, 'simulation_results.json')
        
        self.game.run_simulation(num_hands, output_file)
        
        # Convert game statistics to our format
        stats = {
            'hands_won': [self.game.stats[f"Player {i+1}"].hands_won for i in range(self.game.num_players)],
            'total_profit': [self.game.stats[f"Player {i+1}"].total_profit for i in range(self.game.num_players)],
            'folds': [self.game.stats[f"Player {i+1}"].fold_count for i in range(self.game.num_players)],
            'calls': [self.game.stats[f"Player {i+1}"].call_count for i in range(self.game.num_players)],
            'raises': [self.game.stats[f"Player {i+1}"].raise_count for i in range(self.game.num_players)],
            'all_ins': [self.game.stats[f"Player {i+1}"].all_in_count for i in range(self.game.num_players)],
            'best_hands': [str(self.game.stats[f"Player {i+1}"].best_hand) if self.game.stats[f"Player {i+1}"].best_hand else "None" for i in range(self.game.num_players)]
        }
        
        self.stats_history.append({
            'timestamp': datetime.now(),
            'variant': self.game.four_card_flop,
            'stats': stats
        })
        return stats
    
    def create_win_rate_chart(self, stats: Dict[str, Any]) -> go.Figure:
        """Create win rate visualization using plotly."""
        players = [f"Player {i+1}" for i in range(len(stats['hands_won']))]
        win_rates = [(wins / sum(stats['hands_won'])) * 100 for wins in stats['hands_won']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=players,
                y=win_rates,
                text=[f"{rate:.1f}%" for rate in win_rates],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Win Rates by Player",
            xaxis_title="Player",
            yaxis_title="Win Rate (%)",
            template="plotly_dark"
        )
        
        return fig
    
    def create_action_distribution_chart(self, stats: Dict[str, Any]) -> go.Figure:
        """Create action distribution visualization using plotly."""
        players = [f"Player {i+1}" for i in range(len(stats['folds']))]
        
        fig = go.Figure(data=[
            go.Bar(name='Folds', x=players, y=stats['folds']),
            go.Bar(name='Calls', x=players, y=stats['calls']),
            go.Bar(name='Raises', x=players, y=stats['raises']),
            go.Bar(name='All-ins', x=players, y=stats['all_ins'])
        ])
        
        fig.update_layout(
            barmode='group',
            title="Action Distribution by Player",
            xaxis_title="Player",
            yaxis_title="Number of Actions",
            template="plotly_dark"
        )
        
        return fig
    
    def create_profit_chart(self, stats: Dict[str, Any]) -> go.Figure:
        """Create profit visualization using plotly."""
        players = [f"Player {i+1}" for i in range(len(stats['total_profit']))]
        
        fig = go.Figure(data=[
            go.Bar(
                x=players,
                y=stats['total_profit'],
                text=[f"${profit:,.2f}" for profit in stats['total_profit']],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Total Profit by Player",
            xaxis_title="Player",
            yaxis_title="Profit ($)",
            template="plotly_dark"
        )
        
        return fig
    
    def _format_hand_strength(self, hand_str: str) -> str:
        """Format hand strength string to be more readable."""
        if hand_str == "None":
            return "None"
            
        # Convert card numbers to readable values (0-based index matching Rank enum)
        card_values = {
            0: "2",    # TWO
            1: "3",    # THREE
            2: "4",    # FOUR
            3: "5",    # FIVE
            4: "6",    # SIX
            5: "7",    # SEVEN
            6: "8",    # EIGHT
            7: "9",    # NINE
            8: "10",   # TEN
            9: "Jack", # JACK
            10: "Queen", # QUEEN
            11: "King", # KING
            12: "Ace"   # ACE
        }
        
        # Extract rank and high cards from the string
        import re
        rank_match = re.search(r"HandRank\.(\w+)", hand_str)
        high_cards_match = re.search(r"high_cards=\[([\d, ]+)\]", hand_str)
        
        if not rank_match:
            return hand_str
            
        rank = rank_match.group(1).replace("_", " ").title()
        high_cards = []
        
        if high_cards_match:
            try:
                high_cards = [int(card) for card in high_cards_match.group(1).split(",") if card.strip()]
                high_cards = [card_values.get(card, str(card)) for card in high_cards]  # Use get() with fallback
            except (ValueError, KeyError) as e:
                # If there's any error parsing the cards, just show the rank
                return rank
        
        result = f"{rank}"
        if high_cards:
            if len(high_cards) == 1:
                result += f" (High: {high_cards[0]})"
            else:
                result += f" (High: {', '.join(high_cards)})"
        
        return result

def main():
    app = PokerApp()
    app.render()

if __name__ == "__main__":
    main()
