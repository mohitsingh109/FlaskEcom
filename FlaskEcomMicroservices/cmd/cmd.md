# Deploy Postgres
```
 kubectl apply -f postgres-deployment.yaml
 
 minikube image build -t auth_service:latest .
 
 kubectl apply -f k8s/auth-service-deployment.yaml
 
 Delete: kubectl delete deployment auth-service
 
 kubectl exec -it postgres-f69dc968d-xs8hh -- /bin/bash
 
 psql -U auth_user -d auth_db
 
 CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    previous_price DECIMAL(10, 2),
    in_stock INTEGER DEFAULT 0,
    flash_sale BOOLEAN DEFAULT FALSE,
    product_picture VARCHAR(255),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    product_link INT NOT NULL,
    customer_link INT NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (product_link) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_link) REFERENCES customer(id) ON DELETE CASCADE
);

CREATE TABLE orders (
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

```
---
# Deploy View Service
```
minikube image build -t view_service:latest .

kubectl apply -f k8s/view-service-deployment.yaml

minikube service view-service --url

Delete: kubectl delete deployment view-service 
```


# Deploy Product Service
```
minikube image build -t product_service:latest .

kubectl apply -f k8s/product-service-deployment.yaml

kubectl exec -it postgres-f69dc968d-xs8hh -- /bin/bash

Delete: kubectl delete deployment product-service
```

# Deploy Cart Service
```
minikube image build -t cart_service:latest .

kubectl apply -f k8s/cart-service-deployment.yaml

Delete: kubectl delete deployment cart-service

kubectl exec -it postgres-f69dc968d-xs8hh -- /bin/bash


```

# Deploy Order Service
```
minikube image build -t order_service:latest .

kubectl apply -f k8s/order-service-deployment.yaml

Delete: kubectl delete deployment order-service

```