Prerequisites:

    Install and configure Kafka and start it locally or on a server.
    kafka config: https://www.geeksforgeeks.org/how-to-install-and-run-apache-kafka-on-windows/
    Install Python Kafka library:
    pip install confluent-kafka

Testing the system:
    RUN ALL IN SEPARATE CMD PROMPTS !!
    Start Kafka:

    Start Zookeeper
    # bin/zookeeper-server-start.sh config/zookeeper.properties
    Start Kafka
    # bin/kafka-server-start.sh config/server.properties

    Run the Producer:

    python producer_microservice.py

    Run the Consumer:

    python consumer_microservice.py
