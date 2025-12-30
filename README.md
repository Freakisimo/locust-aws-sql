# Locust Performance Testing Tool (Hybrid Local/AWS)

This project provides an integrated environment for running load tests against a SQL database using Locust, simulating AWS services (CloudWatch, Secrets Manager, RDS) locally via LocalStack, and visualizing results in a custom Streamlit dashboard.

## Features

### 🚀 Locust Runner
-   **Interactive Control Panel:** Configure, start, and stop tests via UI.
-   **Execution Timer:** Live countdown and progress bar for test duration.
-   **Dynamic Query Selection:** Run specific SQL files (e.g., `heavy_analytic_query.sql`) by name.
-   **Robust Process Management:** Handles long-running tests with proper log buffering.

### 📊 Real-time Monitoring & History
-   **Live CloudWatch Metrics:** Visualizes CPU, Connections, IOPS, and Storage usage (simulated via LocalStack).
-   **Log Analysis:** Query "CloudWatch Logs" for slow queries and errors directly from the dashboard.
-   **Test Persistence:** Automatically saves test results to a history file (`test_history.csv`).
-   **History Dashboard:** View trends of response times and failures across all past executions.

### 🗄️ Database Environment
-   **Expanded Schema:** Includes `users`, `products`, `orders`, `reviews`, and `categories`.
-   **Large Dataset:** Automatically seeds thousands of records for realistic testing.
-   **Complex Queries:** Includes pre-built heavy analytical and slow search queries to stress-test the DB.

## Quick Start

1.  **Clone the repository.**
2.  **Start the environment:**
    ```bash
    docker-compose up --build
    ```
3.  **Access the Dashboard:**
    Open [http://localhost:8501](http://localhost:8501) in your browser.

## Architecture

*   **App Service:** Streamlit dashboard + Locust runner.
*   **DB Service:** PostgreSQL 13 (simulating RDS).
*   **LocalStack:** Simulates AWS CloudWatch and Secrets Manager.

## Configuration

You can configure the environment behaviour using environment variables in `docker-compose.yml` or your `.env` file.

### Hybrid Mode (LocalStack vs Real AWS)
*   **`USE_LOCALSTACK=true`** (Default): The application connects to the local LocalStack container for CloudWatch and Secrets Manager. Ideal for offline development and testing.
*   **`USE_LOCALSTACK=false`**: The application ignores the local endpoint and connects to real AWS services using your configured credentials (`~/.aws/credentials` or env vars). Use this for integration testing or staging.

## Features Guide

### Running a Test
1.  Go to the **Locust Runner** page.
2.  Select the queries you want to test (e.g., `heavy_analytic_query.sql`).
3.  Set users, spawn rate, and run time (e.g., `10m`).
4.  Click **Start Test**.
5.  Watch the timer and real-time status.

### Viewing Results
*   **Current Test:** Results appear automatically in the Runner page when the test finishes.
*   **History:** Go to the **History** page to see a table of all past runs and performance trend charts.
*   **Database Health:** Go to **Database Performance** to see simulated CloudWatch metrics and query logs.

## Project Structure

*   `pages/`: Streamlit dashboard pages.
*   `queries/`: SQL files available for testing.
*   `db_setup/`: Schema and data seeding scripts.
*   `locustfile.py`: Logic for executing selected queries.
*   `init-localstack.sh`: Configures simulated AWS environment.
