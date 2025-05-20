import subprocess

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel,QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatusWidget(QWidget):
    def __init__(self, metrics):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.launch_button = QPushButton("Run")
        self.layout.addWidget(self.launch_button)

        # Connect to lambda: run process and disable button
        self.launch_button.clicked.connect(
            lambda _: (subprocess.Popen(["python", "simulation.py"]), self.launch_button.setDisabled(True))
        )

        # Add title
        self.title = QLabel("<b>Node Status Summary</b>")
        self.layout.addWidget(self.title)

        # Add text labels
        self.s_label = QLabel()
        self.i_label = QLabel()
        self.r_label = QLabel()
        self.k_label = QLabel()
        self.hour_label = QLabel()
        self.time_label = QLabel()


        from qtpy.QtWidgets import QGridLayout



        text_grid = QGridLayout()

        # Add labels row by row
        text_grid.addWidget(self.s_label, 0, 0)
        text_grid.addWidget(self.hour_label, 0, 1)

        text_grid.addWidget(self.i_label, 1, 0)
        text_grid.addWidget(self.time_label, 1, 1)

        text_grid.addWidget(self.r_label, 2, 0)
        text_grid.addWidget(QWidget(), 2, 1)  # Empty spacer

        text_grid.addWidget(self.k_label, 3, 0)
        text_grid.addWidget(QWidget(), 3, 1)  # Empty spacer


        self.layout.addLayout(text_grid)

        # Add pie chart
        self.figure = Figure(figsize=(3, 3))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Initial update
        self.update_panel(metrics)

    def update_panel(self, metrics):
        # Update labels
        self.s_label.setText(f"🟢 Susceptible: <b>{metrics['S']:,}</b>")
        self.i_label.setText(f"🔴 Infected: <b>{metrics['I']:,}</b>")
        self.r_label.setText(f"🔵 Recovered: <b>{metrics['R']:,}</b>")
        self.k_label.setText(f"⚫ Killed: <b>{metrics['D']:,}</b>")

        # Update pie chart
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        values = [
            metrics["S"],
            metrics["I"],
            metrics["R"],
            metrics["D"]
        ]
        colors = ["green", "red", "blue", "black"]
        labels = ["", "", "", ""]
        ax.pie(values, labels=labels, colors=colors, startangle=90)
        ax.axis("equal")

        # Update hour and time labels
        h = metrics["h"]
        self.hour_label.setText(f"⏱ Hour: <b>{h}</b>")

        # Convert to clock time (starting from 5:00 PM)
        base_hour = 17
        clock_hour = (base_hour + h) % 24
        am_pm = "AM" if clock_hour < 12 or clock_hour == 24 else "PM"
        display_hour = clock_hour if 1 <= clock_hour <= 12 else (clock_hour - 12 if clock_hour > 12 else 12)
        self.time_label.setText(f"🕒 Time: <b>{display_hour}:00 {am_pm}</b>")


        self.canvas.draw()