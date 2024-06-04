from PyQt5.QtWidgets import (
    QWidget, 
    QHBoxLayout,
    QApplication,
    QFrame
)
from PyQt5.QtGui import QPalette, QPen, QPainter, QBrush, QFont
from PyQt5.QtCore import Qt, QPoint, QRect

from othello.OthelloUtil import getValidMoves, executeMove, isValidMove
import numpy as np


# Constants that will affect how it looks
BOARD_SIZE = 520  # Side length of whole board, including margin
GRID_SIZE = 60  # Side length of a grid, 8x8
PIECE_SIZE = 45  # Diameter of circle that represents a piece
DOT_SIZE = 10  # Dot indicator of possible moves
IND_SIZE = 128  # The score indicator on the left, diameter of circle
IND_BOARD_SIZE = 150  # Same as above, side length of canvas

#margin = (BOARD_SIZE - 10 * GRID_SIZE) // 2  # Should be some 20
margin=GRID_SIZE
padding = (GRID_SIZE - PIECE_SIZE) // 2  # Should be some 10
d_padding = (GRID_SIZE - DOT_SIZE) // 2  # Should be some 25
ind_margin = (IND_BOARD_SIZE - IND_SIZE) // 2


class ReversiUI(QWidget):
    def __init__(self, board, color, resolve):
        global BOARD_SIZE, margin
        self.board=np.array(board)
        BOARD_SIZE=(self.board.shape[0]*GRID_SIZE)+(2*margin)
        self.mycolor=color
        self.color=color
        self.resolve=resolve
        
        # Create layout
        super(ReversiUI, self).__init__()
        self.master = QHBoxLayout()
        self.painter = PaintArea(board=board)
        self.painter.setFocusPolicy(Qt.StrongFocus)
        self.init_ui()

    def init_ui(self):
        # Insert elements into layout
        self.master.addWidget(self.painter)
        
        # Add events
        def boardClick(event):
            """
            Event handler of mouse click on the "game board" canvas
            """
            ex, ey = event.x(), event.y()
            gx, gy = (ex - margin) // GRID_SIZE, (ey - margin) // GRID_SIZE
            rx, ry = ex - margin - gx * GRID_SIZE, ey - margin - gy * GRID_SIZE
            if 0 <= gx < self.board.shape[1] and 0 <= gy < self.board.shape[0] and \
                    abs(rx - GRID_SIZE / 2) < PIECE_SIZE / 2 > abs(ry - GRID_SIZE / 2):
                self.onClickBoard((gx, gy))
        

        self.painter.mouseReleaseEvent = boardClick
        
        self.setLayout(self.master)
        #self.setWindowTitle("iBug Reversi: PyQt5")
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint)

        self.show()
        self.update_board()
        self.setFixedSize(self.size())
    
    def onClickBoard(self, pos):
        """
        Game event handler on clicking the board
        """
        x, y = pos
        if self.color==self.mycolor and isValidMove(self.board, self.color, (y,x)):
            executeMove(self.board, self.color, (y,x))
            self.color=-self.color
            self.update_ui(True)
            self.resolve([y,x])
        
    def renew_board(self, board, color, resolve):
        board=np.array(board)
        self.board=board
        self.resolve=resolve
        self.update_ui(True)
        self.mycolor=color
        self.color=color
        self.update_ui(True)
    
    def update_board(self):
        """
        Wrapped function to update the appearance of the board

        Primarily, setting data for the actual painter function to process
        """
        self.painter.assignBoard(self.board)
        if self.color==self.mycolor:
            self.painter.assignDots(getValidMoves(self.board, self.color))
        else:
            self.painter.assignDots(None)
        self.painter.update()

    def update_ui(self, force=False):
        """
        Workaround of UI getting stuck at waiting AI calculation

        See: https://stackoverflow.com/q/49982509/5958455
        """
        self.update_board()
        if force:
            QApplication.instance().processEvents()

class PaintArea(QWidget):
    """
    The class that handles the drawing of the game board
    """

    def __init__(self, board=None):
        super(PaintArea, self).__init__()
        self.board = board
        self.dots = None
        self.spdots = None

        self.setPalette(QPalette(Qt.white))
        self.setAutoFillBackground(True)
        self.setMinimumSize(BOARD_SIZE, BOARD_SIZE)

        self.penConfig = \
            [Qt.black, 2, Qt.PenStyle(Qt.SolidLine), Qt.PenCapStyle(Qt.RoundCap), Qt.PenJoinStyle(Qt.MiterJoin)]
        self.noPen = \
            QPen(Qt.black, 2, Qt.PenStyle(Qt.NoPen), Qt.PenCapStyle(Qt.RoundCap), Qt.PenJoinStyle(Qt.MiterJoin))
        brushColorFrame = QFrame()
        brushColorFrame.setAutoFillBackground(True)
        brushColorFrame.setPalette(QPalette(Qt.white))
        self.brushConfig = Qt.white, Qt.SolidPattern
        self.update()

    def assignBoard(self, board):
        # Copy the board to avoid accidental change to original board
        self.board = board.copy()

    def assignDots(self, dots):
        # This one won't change, no need to copy
        self.dots = dots


    def paintEvent(self, QPaintEvent):
        """
        Called by QWidget (superclass) when an update event arrives
        """
        if self.board is None:
            raise ValueError("Cannot paint an empty board!")
        p = QPainter(self)

        self.penConfig[0] = Qt.blue
        p.setPen(QPen(*self.penConfig))
        p.setBrush(QBrush(*self.brushConfig))
        # Draw the grids
        for i in range(self.board.shape[0]+1):
            A = QPoint(margin, margin + i * GRID_SIZE)
            B = QPoint(BOARD_SIZE - margin, margin + i * GRID_SIZE)
            p.drawLine(A, B)
            A = QPoint(margin + i * GRID_SIZE, margin)
            B = QPoint(margin + i * GRID_SIZE, BOARD_SIZE - margin)
            p.drawLine(A, B)
        p.setFont(QFont("Arial", GRID_SIZE//3, QFont.Bold))
        for i in range(self.board.shape[0]):
            p.drawText(GRID_SIZE*(i+1), 0, GRID_SIZE, GRID_SIZE, Qt.AlignCenter, chr(ord('A')+i))
            p.drawText(0, GRID_SIZE*(i+1), GRID_SIZE, GRID_SIZE, Qt.AlignCenter, str(i+1))

        self.penConfig[0] = Qt.black
        p.setPen(QPen(*self.penConfig))
        # Draw game pieces
        for i in range(self.board.shape[1]):
            for j in range(self.board.shape[0]):
                if self.board[j][i] == 0:
                    continue
                fillColor = [None, Qt.black, Qt.white]
                p.setBrush(QBrush(fillColor[self.board[j][i]], Qt.SolidPattern))
                p.drawEllipse(QRect(
                    margin + padding + i * GRID_SIZE, margin + padding + j * GRID_SIZE,
                    PIECE_SIZE, PIECE_SIZE))

        # Draw dot indicators if available
        if self.dots is not None:
            p.setPen(self.noPen)
            p.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
            for y, x in self.dots:
                p.drawEllipse(QRect(
                    margin + d_padding + x * GRID_SIZE, margin + d_padding + y * GRID_SIZE,
                    DOT_SIZE, DOT_SIZE))

