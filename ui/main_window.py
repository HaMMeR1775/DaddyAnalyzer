from urllib.parse import urlparse

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Daddy Analyzer")
        self.resize(1600, 950)

        self.setStyleSheet("""
            QMainWindow {
                background: #111315;
            }

            QWidget {
                background: #111315;
                color: #FFFFFF;
                font-family: "Segoe UI";
            }

            QFrame#Sidebar {
                background: #16191D;
                border-right: 1px solid #2A2F36;
            }

            QLabel#Logo {
                font-size: 30px;
                font-weight: 800;
            }

            QLabel#Subtitle {
                color: #8A919D;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 15px;
                text-align: left;
                padding: 14px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background: #2A2015;
                color: #FF8A00;
            }

            QPushButton#AnalyzeButton {
                background: #FF8A00;
                color: #111315;
                font-size: 17px;
                font-weight: 700;
                border-radius: 10px;
                padding: 15px 30px;
            }

            QPushButton#AnalyzeButton:hover {
                background: #FFA733;
            }

            QPushButton#AnalyzeButton:disabled {
                background: #6B430F;
                color: #A0A7B4;
            }

            QLineEdit {
                background: #16191D;
                border: 1px solid #2A2F36;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                padding: 15px;
            }

            QLineEdit:focus {
                border: 1px solid #FF8A00;
            }

            QFrame#Card {
                background: #16191D;
                border: 1px solid #2A2F36;
                border-radius: 12px;
            }

            QLabel#CardTitle {
                color: #8A919D;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#CardValue {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#Status {
                color: #8A919D;
                font-size: 13px;
            }
        """)

        # =================================================
        # MAIN CONTAINER
        # =================================================

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =================================================
        # SIDEBAR
        # =================================================

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(25, 35, 25, 25)

        logo = QLabel(
            '<span style="color:#FFFFFF;">DADDY</span><br>'
            '<span style="color:#FF8A00;">ANALYZER</span>'
        )
        logo.setObjectName("Logo")

        subtitle = QLabel("MYTHIC+ PERFORMANCE COACH")
        subtitle.setObjectName("Subtitle")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(45)

        navigation = [
            "🏠  Dashboard",
            "📊  Reports",
            "🤖  AI Coach",
            "⚔️  Mythic+",
            "👥  Team",
            "👤  My Performance",
            "⚙️  Settings",
        ]

        for text in navigation:
            button = QPushButton(text)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        # =================================================
        # PLAYER PROFILE
        # =================================================

        profile = QFrame()
        profile.setObjectName("Card")

        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(15, 15, 15, 15)

        player_name = QLabel("DADDY#212845")
        player_name.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
        """)

        player_class = QLabel("Balance Druid")
        player_class.setStyleSheet("""
            color: #FF8A00;
            font-size: 13px;
            font-weight: 600;
        """)

        profile_layout.addWidget(player_name)
        profile_layout.addWidget(player_class)

        sidebar_layout.addWidget(profile)

        # =================================================
        # MAIN CONTENT
        # =================================================

        content = QWidget()

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(60, 55, 60, 45)
        content_layout.setSpacing(15)

        welcome = QLabel("Welcome back to Daddy Analyzer.")
        welcome.setStyleSheet("""
            color: #FF8A00;
            font-size: 18px;
            font-weight: 600;
        """)

        title = QLabel(
            'Analyze. Improve. '
            '<span style="color:#FF8A00;">Dominate.</span>'
        )

        title.setStyleSheet("""
            font-size: 46px;
            font-weight: 800;
        """)

        description = QLabel(
            "Paste your Warcraft Logs report URL to get started."
        )

        description.setStyleSheet("""
            color: #A0A7B4;
            font-size: 16px;
        """)

        content_layout.addWidget(welcome)
        content_layout.addWidget(title)
        content_layout.addWidget(description)
        content_layout.addSpacing(25)

        # =================================================
        # URL INPUT + ANALYZE BUTTON
        # =================================================

        analyze_layout = QHBoxLayout()
        analyze_layout.setSpacing(12)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "🔗   Paste your Warcraft Logs URL here..."
        )

        self.analyze_button = QPushButton("⚡  ANALYZE LOGS")
        self.analyze_button.setObjectName("AnalyzeButton")
        self.analyze_button.setFixedWidth(220)

        self.analyze_button.clicked.connect(self.analyze_logs)

        analyze_layout.addWidget(self.url_input)
        analyze_layout.addWidget(self.analyze_button)

        content_layout.addLayout(analyze_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Status")

        content_layout.addWidget(self.status_label)

        # =================================================
        # STATISTICS
        # =================================================

        content_layout.addSpacing(15)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        stats = [
            ("KEYS COMPLETED", "100+"),
            ("BEST KEY", "+16"),
            ("AVERAGE SCORE", "--"),
            ("CURRENT M+", "--"),
        ]

        for name, value in stats:
            card = QFrame()
            card.setObjectName("Card")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)

            card_title = QLabel(name)
            card_title.setObjectName("CardTitle")

            card_value = QLabel(value)
            card_value.setObjectName("CardValue")

            card_layout.addWidget(card_title)
            card_layout.addSpacing(8)
            card_layout.addWidget(card_value)

            stats_layout.addWidget(card)

        content_layout.addLayout(stats_layout)

        # =================================================
        # LOWER PANELS
        # =================================================

        content_layout.addSpacing(20)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        recent = QFrame()
        recent.setObjectName("Card")

        recent_layout = QVBoxLayout(recent)
        recent_layout.setContentsMargins(25, 25, 25, 25)

        recent_title = QLabel("🕐  RECENT ANALYSES")
        recent_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
        """)

        recent_empty = QLabel(
            "\n\nNo analyses yet\n\n"
            "Paste a Warcraft Logs report to get started."
        )

        recent_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recent_empty.setStyleSheet("""
            color: #8A919D;
            font-size: 14px;
        """)

        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(recent_empty)
        recent_layout.addStretch()

        performance = QFrame()
        performance.setObjectName("Card")

        performance_layout = QVBoxLayout(performance)
        performance_layout.setContentsMargins(25, 25, 25, 25)

        performance_title = QLabel("📈  PERFORMANCE OVERVIEW")
        performance_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
        """)

        performance_empty = QLabel(
            "\n\nNo performance data yet\n\n"
            "Your performance will appear here after your first analysis."
        )

        performance_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        performance_empty.setStyleSheet("""
            color: #8A919D;
            font-size: 14px;
        """)

        performance_layout.addWidget(performance_title)
        performance_layout.addWidget(performance_empty)
        performance_layout.addStretch()

        bottom_layout.addWidget(recent)
        bottom_layout.addWidget(performance)

        content_layout.addLayout(bottom_layout)
        content_layout.addStretch()

        # =================================================
        # ADD TO MAIN WINDOW
        # =================================================

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

    # =====================================================
    # ANALYZE LOGS
    # =====================================================

    def analyze_logs(self):
        url = self.url_input.text().strip()

        if not url:
            self.show_status(
                "Please enter a Warcraft Logs report URL.",
                "#FF5D5D"
            )
            return

        if not self.is_valid_warcraft_logs_url(url):
            self.show_status(
                "Invalid URL. Please enter a valid Warcraft Logs report URL.",
                "#FF5D5D"
            )
            return

        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("⏳  CHECKING...")

        self.show_status(
            "✓ Valid Warcraft Logs report URL detected.",
            "#39D353"
        )

        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("⚡  ANALYZE LOGS")

    def is_valid_warcraft_logs_url(self, url):
        try:
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                return False

            hostname = parsed.hostname

            if hostname is None:
                return False

            hostname = hostname.lower()

            if hostname not in (
                "warcraftlogs.com",
                "www.warcraftlogs.com",
            ):
                return False

            if not parsed.path.startswith("/reports/"):
                return False

            report_id = parsed.path.replace("/reports/", "").strip("/")

            if not report_id:
                return False

            return True

        except Exception:
            return False

    def show_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
        """)