"""Application entry point for Currency Converter."""

from src.ui.main_window import MainWindow


def main():
    """Start the Currency Converter desktop application."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
