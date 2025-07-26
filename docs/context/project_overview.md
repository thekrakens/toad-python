# 🐸 TOAD - Track, Optimize, Analyze, Deliver

## Project Vision

TOAD is an enhanced Notion planner with custom Python + AI functionality designed to provide advanced productivity analytics and visualizations that Notion cannot handle natively.

## Core Goals

### Primary Objective
Create a **hybrid productivity system** that:
- Uses **Notion as the source of truth** for task planning and data entry
- Provides **advanced analytics and visualizations** through external processing
- Enables **dynamic, interactive dashboards** that can be embedded back into Notion
- Maintains **device/cloud agnostic access** through Notion's infrastructure

### Key Use Cases

**Daily Workflow:**
1. **Morning Planning**: Enter tasks, set planned timelines, create time blocks with estimated durations
2. **During Work**: Start timers, work on tasks, take notes, log time entries with breaks tracked
3. **Unplanned Events**: Handle unexpected meetings, urgent tasks, distractions, and scope changes
4. **End of Day**: Analyze adherence, efficiency, planning accuracy, and productivity patterns

**Analytics Goals:**
- How well did I complete planned tasks?
- Did tasks take as long as expected?
- How efficient was I (break patterns, focus time)?
- How well did I adhere to my planned schedule?
- How accurate was my time estimation?
- What patterns exist in my productivity?

## Architecture Decision

We chose our hybrid approach because it provides:

### ✅ Benefits
- **Notion's excellent UX** for planning and data entry
- **Unlimited analytical power** without API constraints
- **Advanced visualizations** (interactive timelines, regression analysis, AI insights)
- **Device agnostic access** through Notion
- **Scalable data processing** with local caching
- **Notion embedding** for seamless integration
- **Local storage for advanced charting, predictive features, and historical backups**

### 🔄 Data Flow

The TOAD system employs a hybrid data processing architecture that leverages both Notion's native capabilities and a powerful local processing pipeline.

**1. Data Origination (Notion)**
- **Source of Truth**: All raw data, including tasks, time entries, and other metrics, is manually entered and stored in Notion databases.
- **User Experience**: Notion serves as the primary user interface for data entry and day-to-day planning.

**2. ETL Processing (TOAD)**
- **Extraction**: The TOAD application extracts data from Notion using the official API.
- **Transformation**: The raw data is cleaned, transformed, and enriched using Python (Pandas). This process splits the data into two streams:

**3. Data Destinations**

*   **Stream A: Back to Notion**
    *   **Purpose**: For simple, native visualizations.
    *   **Process**: Aggregated metrics and basic analytics are loaded back into specific Notion databases.
    *   **Use Case**: Powers native Notion charts, tables, and rollups for quick, at-a-glance insights.

*   **Stream B: Local Storage (SQLite)**
    *   **Purpose**: For advanced analytics, long-term storage, and high-performance dashboards.
    *   **Process**: The detailed, transformed data is cached in a local SQLite database.
    *   **Use Case**: Serves as the data source for complex analytics that are beyond Notion's capabilities.

**4. Advanced Analytics & Visualization**
- **Local Analytics Engine**: The locally stored data is fed into our custom analytics engine.
    - **Advanced Analytics**: Performs complex calculations, time-series analysis, and generates detailed metrics.
    - **Predictive Analysis (ML)**: Utilizes machine learning models (e.g., scikit-learn) for forecasting, pattern recognition, and providing predictive insights.
- **Interactive Dashboards**: The results are rendered as interactive dashboards (using Plotly, Flask).
- **Notion Embedding**: These dashboards are then embedded back into Notion pages, providing a seamless user experience that combines Notion's UI with powerful, custom-built visualizations.

**5. Automated Data Ingestion (LLM-Powered)**
- An advanced feature involves using Large Language Models (LLMs) to automate data entry for specific modules (e.g., Finance, Health).
- **Flow**:
    1. Files (e.g., bank statements, workout PDFs) are uploaded to a designated directory.
    2. An LLM parses the file, extracts relevant data.
    3. The structured data is then automatically uploaded to the appropriate Notion database via the TOAD application.

## Technology Stack

### Backend
- **Python**: Core analytics and data processing
- **Pandas/NumPy**: Data transformation and analysis
- **SQLite**: Local caching for performance
- **Notion API**: Data extraction and selective sync

### Web Dashboard
- **Flask**: Web application framework
- **Plotly.js**: Interactive charts and visualizations
- **Bootstrap**: Responsive UI framework
- **SQLite Caching**: Fast data access

### Analytics
- **Matplotlib/Seaborn**: Static visualizations when needed
- **Scikit-learn**: For predictive analysis and ML models.
- **Custom Analytics Engine**: Time block analysis, adherence metrics
- **Future AI/LLM Integration**: Regression analysis, pattern recognition, insights, and automated data parsing.

## TOAD Modules

### 🎯 Productivity Module (ACTIVE - Primary Focus)
**Status: In Development**

Enhance and streamline planning and tracking tasks for the day. ETL process for a Daily Productivity Metrics table that processes task data, time entries, and time blocks to generate comprehensive productivity insights.

**Core Functionality:**
- **Interactive Timeline Dashboard** - Daily view with planned vs actual work visualization
- **Real-time Analytics** - 15+ productivity metrics including adherence, efficiency, time debt
- **Notion Integration** - Seamless data extraction and metrics sync
- **SQLite Caching** - High-performance data processing with smart invalidation

**Advanced Features:**
- **Weekly Analytics** - Productivity trends and pattern analysis
- **Predictive Insights** - Time estimation accuracy and schedule optimization
- **AI Integration** - Pattern recognition and productivity recommendations

**Current Implementation:** Core data structures and ETL processes are being built.

### 🌱 Plant Tracker Module (PLANNED)
**Status: Planning Phase**

This module will track plant health and watering schedules. Data will be manually entered in Notion, and TOAD will process this data to provide notifications and suggested watering schedules. Advanced predictive analytics may be used to account for seasonal needs.

**Core Functionality (Planned):**
- **Plant Database in Notion:** To log watering status and plant health.
- **ETL Process:** To extract and process data from Notion.
- **Watering Schedule:** Provide notifications/updates or suggested watering schedule for each plant.
- **Predictive Analytics:** Account for seasonal needs of specific indoor plants.

### 🏃‍♂️ Health Module (PLANNED)
**Status: Design Phase** - Database schema defined, awaiting implementation

Data entry table for logging daily habits with transformation into metrics suitable for notion visuals and predictive analytics.

**Core Functionality (Planned):**
- **Habit Tracking** - Daily logging of health metrics (weight, calories, activities)
- **Visual Analytics** - Weight trends, calorie balance charts with research-based formulas
- **Predictive Modeling** - Weight loss goal predictions based on historical patterns
- **Routine Analysis** - Correlation between habits and productivity metrics

**Advanced Features (Planned):**
- **Apple Health Integration** - Automatic data import
- **Workout PDF Parsing** - Extract specific lift performance over time
- **LLM Integration** - Daily health tips and goal progress alerts

**Stretch Goals:** PDF workout parsing, lift-specific progress tracking, routine-productivity correlation analysis

### 💰 Finance Tracker Module (PLANNED)
**Status: Planning Phase** - Requirements defined, ready for implementation

Smart spending categorization with goal tracking and automated statement processing.

**Core Functionality (Planned):**
- **Category Goals** - Set spending limits per category
- **Statement Processing** - PDF parsing and intelligent transaction categorization
- **Duplicate Detection** - Handle overlapping statement imports
- **Weekly Analytics** - Spending vs budget visualization in Notion

**Advanced Features (Planned):**
- **Smart Categorization** - ML-based transaction labeling
- **Multi-Institution Support** - Unified view across banks/cards
- **Trend Analysis** - Spending pattern insights and alerts

## Module Status Matrix

| Module | Status | Core Features | Advanced Features | Notion Integration | CLI Commands |
|--------|--------|--------------|-------------------|-------------------|---------------|
| **Productivity** | 🟡 In Progress | ⏳ To Do | ⏳ To Do | 📋 Defined | ⏳ To Do |
| **Plants** | 🔴 Planning | ⏳ To Do | ⏳ To Do | 📋 Defined | ⏳ To Do |
| **Health** | 🔴 Planning | ⏳ To Do | ⏳ To Do | 📋 Defined | ⏳ To Do |
| **Finance** | 🔴 Planning | ⏳ To Do | ⏳ To Do | 📋 Defined | ⏳ To Do |

**Legend:** 🟢 Complete | 🟡 In Progress | 🔴 Planning | ✅ Done | ⏳ To Do | 📋 Designed

## Current Project Structure

```
toad/
├── __init__.py
├── cli.py                 # Unified CLI for all modules
├── config.py             # Cross-module configuration
├── notion_client.py      # Shared Notion API client
├── productivity/         # 🎯 Productivity Module (In Progress)
├── plants/              # 🌱 Plant Tracker Module (Planned)
├── health/              # 🏃‍♂️ Health Module (Planned)
└── finance/             # 💰 Finance Module (Planned)
```
