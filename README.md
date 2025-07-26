# 🐸 TOAD-Python: Track, Optimize, Analyze, Deliver

**TOAD-Python** is an enhanced Notion planner with custom Python + AI functionality designed to provide advanced productivity analytics and visualizations that Notion cannot handle natively.

## Core Goals

- **Hybrid Productivity System**: Combines Notion's excellent UX for data entry with the power of Python for advanced analytics.
- **Advanced Analytics**: Provides deep insights into productivity patterns, efficiency, and adherence to goals.
- **Dynamic Dashboards**: Generates interactive visualizations that can be embedded back into Notion.

## Key Features

- **Productivity Module**: Track tasks, time entries, and generate 15+ productivity metrics.
- **Plant Tracker Module**: Monitor plant health and watering schedules.
- **Health & Finance Modules**: Planned modules for tracking health and financial data.
- **AI Integration**: Leverage LLMs for pattern recognition, insights, and automated data parsing.

## Getting Started

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/toad-python.git
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up your `.env` file with your Notion API keys.
4.  Run the CLI:
    ```bash
    python -m toad.cli --help
    ```

## Usage

The primary interface is the command-line tool. Here are a few examples:

-   **Sync daily metrics**:
    ```bash
    python -m toad.cli metrics sync
    ```
-   **List plants**:
    ```bash
    python -m toad.cli plants list
    ```

---

*This project is currently under active development.*
