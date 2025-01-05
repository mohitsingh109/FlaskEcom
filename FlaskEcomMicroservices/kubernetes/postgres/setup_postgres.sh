#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

# Set deployment and database variables
DEPLOYMENT_FILE="postgres-deployment.yaml"
DB_USER="auth_user"
DB_NAME="auth_db"

# Apply PostgreSQL deployment
echo "Applying PostgreSQL deployment from $DEPLOYMENT_FILE"
kubectl apply -f $DEPLOYMENT_FILE
if [ $? -ne 0 ]; then
  echo "Error: Failed to apply PostgreSQL deployment."
  exit 1
fi

# Wait for the PostgreSQL pod to be ready
echo "Waiting for PostgreSQL pod to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
if [ $? -ne 0 ]; then
  echo "Error: PostgreSQL pod did not become ready in time."
  exit 1
fi

# Get the name of the running PostgreSQL pod
POSTGRES_POD=$(kubectl get pods -l app=postgres -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POSTGRES_POD" ]; then
  echo "Error: Could not find PostgreSQL pod."
  exit 1
fi

echo "PostgreSQL pod found: $POSTGRES_POD"

# Define SQL commands
SQL_COMMANDS=$(cat <<EOF
CREATE TABLE IF NOT EXISTS customer (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    previous_price DECIMAL(10, 2),
    in_stock INTEGER DEFAULT 0,
    flash_sale BOOLEAN DEFAULT FALSE,
    product_picture VARCHAR(255),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    product_link INT NOT NULL,
    customer_link INT NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (product_link) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_link) REFERENCES customer(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    payment_id VARCHAR(100),
    product_link INT NOT NULL,
    customer_link INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product FOREIGN KEY (product_link) REFERENCES product(id) ON DELETE CASCADE,
    CONSTRAINT fk_customer FOREIGN KEY (customer_link) REFERENCES customer(id) ON DELETE CASCADE
);
EOF
)

# Run the SQL commands inside the PostgreSQL pod
echo "Executing SQL commands inside PostgreSQL pod..."
kubectl exec -it $POSTGRES_POD -- bash -c "echo \"$SQL_COMMANDS\" | psql -U $DB_USER -d $DB_NAME"

if [ $? -eq 0 ]; then
  echo "Tables created successfully."
else
  echo "Error: Failed to create tables."
  exit 1
fi
