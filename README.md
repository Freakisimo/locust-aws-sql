# Locust Performance Testing Tool (Hybrid Local/AWS)

This project provides an integrated environment for running load tests against a SQL database using Locust, simulating AWS services (CloudWatch, Secrets Manager, RDS) locally via LocalStack, and visualizing results in a custom Streamlit dashboard.

## Features

### 🏠 Dashboard Home
- **Performance Overview:** Key metrics (Average Response Time, Success Rate) from the last test.
- **Comparative Analysis:** Visual indicators (deltas) comparing current results against historical averages.
- **📜 Test Run History:** Complete history of executions with CSV export functionality.

### 🚀 Locust Runner
- **Interactive Control Panel:** Configure, start, and stop tests via UI.
- **Selection Controls:** Easily select specific queries or use "Select All" functionality.
- **Execution Timer:** Live countdown and progress bar for test duration.
- **Bottleneck Detection:** Top 5 slowest queries identified automatically in real-time.

### 📊 Database Performance
- **Live CloudWatch Metrics:** Visualizes CPU, Connections, IOPS, and Storage usage (Real AWS or LocalStack).
- **Auto-Refresh:** Dashboard updates every 30 seconds to show the latest infrastructure health.
- **Log Analysis:** Integrated RDS logs (Slow Query, Error, General) directly in the dashboard.

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

*   **App Service:** Streamlit dashboard (v1.x) + Locust (v2.x).
*   **DB Service:** PostgreSQL 13 (simulating RDS locally).
*   **LocalStack:** Simulates AWS CloudWatch and Secrets Manager for local development.
*   **AWS Integration:** Native support for real RDS, Secrets Manager, and CloudWatch.

## Configuration

You can configure the environment behaviour using environment variables in `docker-compose.yml` or your `.env` file.

### Hybrid Mode (LocalStack vs Real AWS)
*   **`USE_LOCALSTACK=true`** (Default): The application connects to the local LocalStack container. Ideal for offline development.
    - **Queries:** Pre-built queries in the `queries/` directory are designed to work with the local schema and sample data.
*   **`USE_LOCALSTACK=false`**: The application connects to real AWS services.
    - **Authentication:** Mounts `~/.aws` for seamless integration with local profiles.
    - **Secrets:** Fetches DB credentials securely from AWS Secrets Manager.
    - **Monitoring:** Pulls real metrics from CloudWatch (Last 60 mins).
    - **Custom Queries:** When testing against a production or staging RDS instance, ensure you add your specific `.sql` files to the `queries/` directory to analyze the performance of your own business logic.

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
