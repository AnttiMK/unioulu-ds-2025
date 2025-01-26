NOTE: This folder is obsolete as of ex2, left only for reference purposes.

Prerequisites:

    Install and configure Kafka and start it locally or on a server.
    kafka config: https://www.geeksforgeeks.org/how-to-install-and-run-apache-kafka-on-windows/
    Install Python Kafka library:
    pip install confluent-kafka

Testing the system:
    RUN ALL IN SEPARATE CMD PROMPTS !!
    Start Kafka:

    Start Zookeeper
    # .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
    Start Kafka
    # .\bin\windows\kafka-server-start.bat .\config\server.properties

    Run the Producer:

    python producer.py

    Run the Consumer:

    python consumer.py
