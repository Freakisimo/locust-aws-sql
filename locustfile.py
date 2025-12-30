import time
import os
import random
from locust import User, task, between, events
import psycopg2
from utils import get_secret


class SqlUser(User):
    wait_time = between(1, 5)

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        credentials = get_secret()
        self.connection = psycopg2.connect(
            host=credentials['host'],
            dbname=credentials['dbname'],
            user=credentials['username'],
            password=credentials['password'],
            port=credentials['port']
        )
        self.cursor = self.connection.cursor()
        
        # Load queries from the 'queries' directory
        self.queries = []
        queries_to_run = os.environ.get("QUERIES_TO_RUN")
        if queries_to_run:
            selected_queries = queries_to_run.split(",")
            for filename in selected_queries:
                with open(os.path.join("queries", filename), 'r') as f:
                    self.queries.append((filename, f.read()))
        else:
            for filename in os.listdir("queries"):
                if filename.endswith(".sql"):
                    with open(os.path.join("queries", filename), 'r') as f:
                        self.queries.append((filename, f.read()))

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        if self.connection:
            self.cursor.close()
            self.connection.close()

    @task
    def execute_query_from_file(self):
        if not self.queries:
            return

        filename, query = random.choice(self.queries)
        
        start_time = time.time()
        try:
            self.cursor.execute(query)
            self.cursor.fetchone()
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="sql",
                name=filename, # Use the filename as the name
                response_time=total_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="sql",
                name=filename, # Use the filename as the name
                response_time=total_time,
                response_length=0,
                exception=e,
            )