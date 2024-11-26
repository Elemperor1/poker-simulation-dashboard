# Poker Simulation Dashboard

An interactive, real-time Texas Hold'em poker simulation dashboard built with Streamlit. The application provides comprehensive visualization of poker game dynamics, player statistics, and hand-by-hand analysis.

## Features

- Interactive Streamlit-based dashboard
- Real-time game visualization and statistics
- Support for 2-9 players
- Configurable game parameters:
  - Initial stack sizes
  - Blind levels
  - Number of hands to play
- Detailed player tracking:
  - Stack sizes
  - Position tracking (BTN, SB, BB, UTG, MP, CO)
  - Action distributions (Fold/Call/Raise)
  - Profit/Loss over time
- Event-based gameplay with comprehensive logging
- Modern, responsive UI with Plotly charts

## Requirements

- Python 3.13+
- Required packages (install via `pip install -r requirements.txt`):
  - streamlit
  - plotly
  - pandas
  - numpy
  - rich
  - seaborn

## Installation

1. Clone the repository
2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit dashboard:
```bash
streamlit run main.py
```

### Dashboard Controls

1. Game Configuration (Sidebar):
   - Number of players (2-9)
   - Initial stack size
   - Small blind amount
   - Big blind amount
   - "Start New Game" button to reset all parameters

2. Game Controls:
   - Number of hands to play (1-100)
   - "Play Hands" button to run simulation

### Dashboard Sections

1. Game Statistics:
   - Current player stacks and positions
   - Profit/Loss chart over time
   - Action distribution analysis

2. Game Events:
   - Hand results with winners
   - Recent game events log
   - Real-time updates

## Statistics Tracked

- Per-player statistics:
  - Current stack
  - Position
  - Action status (Active/Folded)
  - Current bet
  - Cumulative profit/loss

- Game-level statistics:
  - Hand number
  - Pot size
  - Action distributions
  - Win/loss patterns

## Implementation Details

The simulation uses:
- Event-based architecture for game state tracking
- Streamlit session state for persistent data
- Plotly for interactive visualizations
- Pandas for data management
- Rich for enhanced console output

## Future Enhancements

- Advanced player strategies
- Hand history export
- More detailed hand analysis
- Multi-table support
- Tournament mode
