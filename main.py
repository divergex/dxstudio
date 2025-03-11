import sys
from datetime import datetime

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

from dxlib.interfaces import MarketInterface
from dxlib.interfaces.external import investing_com


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the UI
        self.api: MarketInterface = investing_com.InvestingCom()
        self.setWindowTitle("Financial App")
        self.setGeometry(100, 100, 400, 300)

        # Create a vertical layout
        layout = QVBoxLayout()

        # Label to display results
        self.result_label = QLabel("Result will appear here", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        # Button to trigger the backend function
        self.call_button = QPushButton("Call Financial Function", self)
        self.call_button.clicked.connect(self.call_backend_function)
        layout.addWidget(self.call_button)

        # Set the layout for the main window
        self.setLayout(layout)

    def call_backend_function(self):
        # Call a function from your Python financial library
        # Replace 'some_function' with the actual function you want to call
        result = self.api.historical("AAPL", datetime(2021, 1, 1), datetime(2021, 12, 31))

        # Display the result in the label
        self.result_label.setText(f"Result: {result}")
        print(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
