from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QLabel, QPushButton, QGridLayout,
                                 QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from typing import List, Dict, Optional
from .game import PokerGame
from .deck import Card
import sys

class CardWidget(QFrame):
    """Widget to display a playing card."""
    def __init__(self, card: Optional[Card] = None):
        super().__init__()
        self.card = card
        self.setMinimumSize(60, 90)
        self.setMaximumSize(60, 90)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.card:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set color based on suit
        if self.card.suit.value in "♥♦":
            color = QColor(255, 0, 0)  # Red for hearts and diamonds
        else:
            color = QColor(0, 0, 0)    # Black for clubs and spades

        painter.setPen(QPen(color))
        painter.setFont(QFont("Arial", 12))

        # Draw rank and suit
        text = f"{self.card.rank.value}{self.card.suit.value}"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

class PlayerWidget(QFrame):
    """Widget to display a player's information and cards."""
    def __init__(self, name: str, position: int):
        super().__init__()
        self.name = name
        self.position = position
        self.stack = 1000.0
        self.cards: List[CardWidget] = []
        self.is_active = True
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Player info
        info_layout = QHBoxLayout()
        self.name_label = QLabel(self.name)
        self.stack_label = QLabel(f"${self.stack:.2f}")
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.stack_label)
        layout.addLayout(info_layout)

        # Cards
        cards_layout = QHBoxLayout()
        for _ in range(2):
            card_widget = CardWidget()
            self.cards.append(card_widget)
            cards_layout.addWidget(card_widget)
        layout.addLayout(cards_layout)

        # Status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: #f0f0f0;")

    def update_cards(self, cards: List[Card]):
        """Update the displayed cards."""
        for i, card in enumerate(cards):
            self.cards[i].card = card
            self.cards[i].update()

    def update_status(self, status: str, stack: float):
        """Update player status and stack."""
        self.status_label.setText(status)
        self.stack = stack
        self.stack_label.setText(f"${self.stack:.2f}")

    def clear(self):
        """Clear cards and status."""
        for card_widget in self.cards:
            card_widget.card = None
            card_widget.update()
        self.status_label.setText("")

class PokerTable(QWidget):
    """Widget to display the poker table with community cards and pot."""
    def __init__(self):
        super().__init__()
        self.community_cards: List[CardWidget] = []
        self.pot = 0.0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Community cards
        cards_layout = QHBoxLayout()
        for _ in range(5):
            card_widget = CardWidget()
            self.community_cards.append(card_widget)
            cards_layout.addWidget(card_widget)
        layout.addLayout(cards_layout)

        # Pot
        self.pot_label = QLabel("Pot: $0.00")
        self.pot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pot_label)

        self.setLayout(layout)

    def update_community_cards(self, cards: List[Card]):
        """Update the community cards display."""
        for i in range(len(self.community_cards)):
            self.community_cards[i].card = cards[i] if i < len(cards) else None
            self.community_cards[i].update()

    def update_pot(self, amount: float):
        """Update the pot amount."""
        self.pot = amount
        self.pot_label.setText(f"Pot: ${self.pot:.2f}")

    def clear(self):
        """Clear community cards and pot."""
        for card_widget in self.community_cards:
            card_widget.card = None
            card_widget.update()
        self.pot = 0.0
        self.pot_label.setText("Pot: $0.00")

class PokerGUI(QMainWindow):
    """Main window for the poker game visualization."""
    def __init__(self):
        super().__init__()
        self.game = PokerGame(num_players=6)
        self.players: List[PlayerWidget] = []
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_hand)
        self.hand_delay = 2000  # 2 seconds between hands

    def setup_ui(self):
        self.setWindowTitle("Poker Simulation")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        layout.addLayout(control_layout)

        # Poker table
        self.table = PokerTable()
        layout.addWidget(self.table)

        # Players
        players_layout = QGridLayout()
        for i in range(6):
            player = PlayerWidget(f"Player {i+1}", i)
            self.players.append(player)
            row = 1 if i < 3 else 0
            col = i % 3
            players_layout.addWidget(player, row, col)
        layout.addLayout(players_layout)

    def start_simulation(self):
        """Start the poker simulation."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.timer.start(self.hand_delay)

    def stop_simulation(self):
        """Stop the poker simulation."""
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def play_hand(self):
        """Play one hand of poker and update the display."""
        # Reset display
        self.table.clear()
        for player in self.players:
            player.clear()

        # Play the hand
        winners = self.game.play_hand()

        # Update community cards
        self.table.update_community_cards(self.game.community_cards)
        self.table.update_pot(self.game.pot)

        # Update players
        for i, game_player in enumerate(self.game.players):
            gui_player = self.players[i]
            gui_player.update_cards(game_player.hole_cards)
            status = "Folded" if not game_player.is_active else "Active"
            if any(winner[0] == game_player for winner in winners):
                status = "Winner!"
            gui_player.update_status(status, game_player.stack)

def run_gui():
    """Run the poker GUI application."""
    app = QApplication(sys.argv)
    window = PokerGUI()
    window.show()
    sys.exit(app.exec())
