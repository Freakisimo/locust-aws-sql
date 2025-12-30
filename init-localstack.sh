#!/bin/bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Create a mock secret
aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name "${SECRET_NAME:-locust/rds/credentials}" \
    --secret-string '{"username":"postgres","password":"password","engine":"postgres","host":"db","port":5432,"dbname":"postgres"}' \
    --region "$AWS_DEFAULT_REGION"

# Generate 60 minutes of time-series metrics for the RDS instance
echo "Generating time-series metrics..."
for i in {0..60}; do
    # Calculate timestamp for 'i' minutes ago
    T_STAMP=$(date -u -d "$i minutes ago" +%Y-%m-%dT%H:%M:%SZ)
    
    # CPU: varies between 5% and 15%
    CPU_VAL=$(awk -v min=5 -v max=15 'BEGIN{srand(); print min+rand()*(max-min)}')
    # Connections: stable at 2
    CONN_VAL=2
    # IOPS: varies between 10 and 50
    IOPS_R=$(awk -v min=10 -v max=50 'BEGIN{srand(); print min+rand()*(max-min)}')
    IOPS_W=$(awk -v min=5 -v max=30 'BEGIN{srand(); print min+rand()*(max-min)}')
    # Storage: 20GB (in bytes)
    STORAGE_VAL=21474836480

    aws --endpoint-url=http://localhost:4566 cloudwatch put-metric-data \
        --namespace "AWS/RDS" \
        --metric-data "[
            {\"MetricName\": \"CPUUtilization\", \"Dimensions\": [{\"Name\": \"DBInstanceIdentifier\", \"Value\": \"$DB_INSTANCE_IDENTIFIER\"}], \"Timestamp\": \"$T_STAMP\", \"Value\": $CPU_VAL, \"Unit\": \"Percent\"},
            {\"MetricName\": \"DatabaseConnections\", \"Dimensions\": [{\"Name\": \"DBInstanceIdentifier\", \"Value\": \"$DB_INSTANCE_IDENTIFIER\"}], \"Timestamp\": \"$T_STAMP\", \"Value\": $CONN_VAL, \"Unit\": \"Count\"},
            {\"MetricName\": \"ReadIOPS\", \"Dimensions\": [{\"Name\": \"DBInstanceIdentifier\", \"Value\": \"$DB_INSTANCE_IDENTIFIER\"}], \"Timestamp\": \"$T_STAMP\", \"Value\": $IOPS_R, \"Unit\": \"Count/Second\"},
            {\"MetricName\": \"WriteIOPS\", \"Dimensions\": [{\"Name\": \"DBInstanceIdentifier\", \"Value\": \"$DB_INSTANCE_IDENTIFIER\"}], \"Timestamp\": \"$T_STAMP\", \"Value\": $IOPS_W, \"Unit\": \"Count/Second\"},
            {\"MetricName\": \"FreeStorageSpace\", \"Dimensions\": [{\"Name\": \"DBInstanceIdentifier\", \"Value\": \"$DB_INSTANCE_IDENTIFIER\"}], \"Timestamp\": \"$T_STAMP\", \"Value\": $STORAGE_VAL, \"Unit\": \"Bytes\"}
        ]" \
        --region "$AWS_DEFAULT_REGION"
done

# Create CloudWatch Log Groups and Streams
DB_LOG_GROUPS="error slowquery general"

for LOG_TYPE in $DB_LOG_GROUPS; do
    LOG_GROUP="/aws/rds/instance/$DB_INSTANCE_IDENTIFIER/$LOG_TYPE"
    echo "Creating Log Group: $LOG_GROUP"
    aws --endpoint-url=http://localhost:4566 logs create-log-group --log-group-name "$LOG_GROUP" --region "$AWS_DEFAULT_REGION"
    aws --endpoint-url=http://localhost:4566 logs create-log-stream --log-group-name "$LOG_GROUP" --log-stream-name "${LOG_TYPE}-stream" --region "$AWS_DEFAULT_REGION"
done

# Put mock log events using JSON for better handling of spaces
TIMESTAMP=$(date +%s000)

aws --endpoint-url=http://localhost:4566 logs put-log-events \
    --log-group-name "/aws/rds/instance/$DB_INSTANCE_IDENTIFIER/error" \
    --log-stream-name "error-stream" \
    --log-events "[{\"timestamp\": $TIMESTAMP, \"message\": \"[ERROR] Database started successfully (mock log)\"}]" \
    --region "$AWS_DEFAULT_REGION"

aws --endpoint-url=http://localhost:4566 logs put-log-events \
    --log-group-name "/aws/rds/instance/$DB_INSTANCE_IDENTIFIER/slowquery" \
    --log-stream-name "slowquery-stream" \
    --log-events "[{\"timestamp\": $TIMESTAMP, \"message\": \"[SLOW] duration: 1540ms statement: SELECT * FROM orders JOIN users ON users.id = orders.user_id WHERE amount > 500;\"}]" \
    --region "$AWS_DEFAULT_REGION"

echo "LocalStack initialized with Secret, CloudWatch metrics, and expanded Logs."
