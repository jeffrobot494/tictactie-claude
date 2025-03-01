# Tic Tac Toe vs Claude

An interactive Tic Tac Toe game that lets you play against Claude AI, with visibility into Claude's thinking process.

## Features

- Play Tic Tac Toe against Claude AI
- See Claude's reasoning for each move
- Choose to play as X or O
- Score tracking
- Clean, responsive interface

## How to Play

1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

2. Run the game:
   ```
   streamlit run tictactoe.py
   ```

3. Enter your Anthropic API key when prompted

4. Play the game by clicking on the board to place your marker

## Technical Details

This game uses:
- Streamlit for the web interface
- Anthropic's Claude API for the AI opponent
- The game allows Claude full control over its moves, creating an interesting opponent that may occasionally make mistakes

## Requirements

- Python 3.8+
- Streamlit
- Anthropic API key

## License

MIT