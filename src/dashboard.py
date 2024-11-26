import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import json
from pathlib import Path

def format_cards(cards):
    """Format cards for display."""
    if not cards:
        return "[]"
    
    if isinstance(cards[0], str):
        return " ".join(cards)
    
    suit_symbols = {
        'hearts': '♥',
        'diamonds': '♦',
        'clubs': '♣',
        'spades': '♠'
    }
    
    formatted = []
    for card in cards:
        rank, suit = card
        symbol = suit_symbols.get(suit.lower(), suit)
        formatted.append(f"{rank}{symbol}")
    
    return " ".join(formatted)

def get_player_number(player_str):
    """Extract player number from player string (e.g., 'Player 1' -> 0)"""
    try:
        return int(player_str.split()[1]) - 1
    except:
        return -1

def display_hand(hand):
    """Display a single hand of poker."""
    # Community Cards
    st.markdown("### Community Cards")
    if hand.get('community_cards'):
        st.markdown(" ".join(hand['community_cards']))
    else:
        st.markdown("*No community cards*")

    # Pot Size
    st.markdown("### Pot")
    st.markdown(f"${hand.get('pot_size', 0):.2f}")

    # Player Information
    st.markdown("### Players")
    
    # Create a grid of player cards
    cols = st.columns(3)
    
    # Check if we have the new format with detailed player info
    if 'players' in hand:
        players_data = [p for p in hand['players'] if p['name'].startswith('Player')]
    else:
        # Create player data from winners info for backwards compatibility
        players_data = []
        for i in range(6):
            player_name = f"Player {i + 1}"
            player_data = {
                'name': player_name,
                'hole_cards': next((w['hole_cards'] for w in hand['winners'] if w['player'] == player_name), []),
                'folded': True,  # Assume folded if not a winner
                'is_active': False
            }
            players_data.append(player_data)
        
        # Mark winners as not folded and active
        for winner in hand['winners']:
            player_data = next(p for p in players_data if p['name'] == winner['player'])
            player_data['folded'] = False
            player_data['is_active'] = True
    
    # Display player information
    for i, player_data in enumerate(players_data):
        with cols[i % 3]:
            st.markdown(f"**{player_data['name']}**")
            if player_data['hole_cards']:
                st.markdown(f"**Cards:** {' '.join(player_data['hole_cards'])}")
            if 'stack' in player_data:
                st.markdown(f"**Stack:** ${player_data['stack']:.2f}")
            
            # Check if this player is a winner
            winner_data = next((w for w in hand['winners'] if w['player'] == player_data['name']), None)
            if winner_data:
                st.markdown(f"**Winnings:** ${winner_data['winnings']:.2f}")
                st.markdown("**🏆 Winner!**")
            elif not player_data.get('is_active', True):
                if player_data.get('folded', True):
                    st.markdown("*Folded*")
                else:
                    st.markdown("*Not Active*")
            
            st.markdown("---")

def run_dashboard(results_dir: str = 'results'):
    """Run the poker analysis dashboard."""
    st.set_page_config(page_title="Poker Simulation Analysis", layout="wide")
    
    st.title("🎲 Poker Simulation Analysis Dashboard")
    
    # Load data
    data = {'three_card': [], 'four_card': []}
    results_path = Path(results_dir)
    
    for variant in ['three_card', 'four_card']:
        file_path = results_path / f"{variant}_results.jsonl"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        try:
                            hand_data = json.loads(line.strip())
                            data[variant].append(hand_data)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                st.error(f"Error loading {variant} data: {str(e)}")
    
    # Sidebar for filtering
    st.sidebar.header("Filters")
    variant = st.sidebar.selectbox(
        "Select Variant",
        ["three_card", "four_card"],
        format_func=lambda x: "Three Card Flop" if x == "three_card" else "Four Card Flop"
    )
    
    if not data[variant]:
        st.error(f"No data available for {variant} variant")
        return

    # Process data
    df = pd.DataFrame(data[variant])
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Hand Replay", "Player Performance", "Hand Analysis", "Betting Patterns"])
    
    # Hand Replay Tab
    with tab1:
        st.subheader("Hand Replay")
        
        # Hand selector
        total_hands = len(data[variant])
        hand_idx = st.slider("Select Hand", 0, total_hands - 1, 0)
        
        # Get the selected hand data
        hand = data[variant][hand_idx]
        
        display_hand(hand)
    
    # Player Performance Tab
    with tab2:
        st.subheader("Player Performance Analysis")
        
        # Calculate player statistics
        player_stats = []
        for i in range(6):
            player_name = f"Player {i + 1}"
            wins = sum(1 for hand in data[variant] 
                      if any(w['player'] == player_name for w in hand['winners']))
            total_profit = sum(w['winnings'] for hand in data[variant]
                             for w in hand['winners'] if w['player'] == player_name)
            
            player_stats.append({
                'player_id': i,
                'player_name': player_name,
                'wins': wins,
                'win_rate': (wins / len(df)) * 100 if len(df) > 0 else 0,
                'total_profit': total_profit
            })
        
        player_stats_df = pd.DataFrame(player_stats)
        
        # Win rates
        fig = px.bar(player_stats_df, 
                    x='player_name', 
                    y='win_rate',
                    title='Player Win Rates (%)',
                    labels={'player_name': 'Player', 'win_rate': 'Win Rate (%)'},
                    color='win_rate')
        st.plotly_chart(fig)
        
        # Distribution of wins
        fig = px.pie(player_stats_df, 
                    values='wins', 
                    names='player_name',
                    title='Distribution of Wins')
        st.plotly_chart(fig)
        
        # Profit chart
        fig = px.bar(player_stats_df, 
                    x='player_name', 
                    y='total_profit',
                    title='Total Profit by Player ($)',
                    labels={'player_name': 'Player', 'total_profit': 'Total Profit ($)'},
                    color='total_profit')
        st.plotly_chart(fig)
    
    # Hand Analysis Tab
    with tab3:
        st.subheader("Hand Analysis")
        
        # Pot size statistics
        stats = {
            'Average Pot': f"${df['pot_size'].mean():.2f}",
            'Median Pot': f"${df['pot_size'].median():.2f}",
            'Largest Pot': f"${df['pot_size'].max():.2f}",
            'Smallest Pot': f"${df['pot_size'].min():.2f}"
        }
        
        cols = st.columns(len(stats))
        for col, (label, value) in zip(cols, stats.items()):
            col.metric(label, value)
    
    # Betting Patterns Tab
    with tab4:
        st.subheader("Betting Pattern Analysis")
        
        # Pot size distribution
        fig = px.histogram(df, 
                          x='pot_size', 
                          nbins=50,
                          title='Pot Size Distribution',
                          labels={'pot_size': 'Pot Size ($)'})
        st.plotly_chart(fig)
        
        # Pot size over time
        df_with_index = df.reset_index()
        fig = px.line(df_with_index, 
                     x='index', 
                     y='pot_size',
                     title='Pot Size Evolution Over Time',
                     labels={'index': 'Hand Number', 'pot_size': 'Pot Size ($)'})
        st.plotly_chart(fig)

if __name__ == "__main__":
    run_dashboard()
