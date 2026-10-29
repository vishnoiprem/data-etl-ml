# Custom Flink image with Kafka + JDBC connectors and Python UDF support.
# Based on flink:1.17.1-scala_2.12-java11.
#
# We pull the connector jars directly from Maven Central and place them
# in /opt/flink/lib/ so the sql-client can resolve the 'kafka' and 'jdbc'
# DynamicTableFactory identifiers. We also install Python for PyFlink UDFs.

FROM flink:1.17.1-scala_2.12-java11

ARG KAFKA_CONNECTOR=3.0.2-1.17
ARG POSTGRES_DRIVER=42.7.3

USER root

# Install Python for PyFlink UDFs (the `env.python.executable=python3` config
# in flink-conf.yaml points to /usr/bin/python3).
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/python3 /usr/bin/python || true

# Install Python deps for PyFlink UDFs (minimal — the UDF only uses stdlib math)
# Pin a known-compatible version of apache-flink for 1.17.
RUN pip3 install --no-cache-dir \
    "apache-flink==1.17.1" || echo "WARN: pip install apache-flink failed (continuing — pyflink comes preinstalled in some flink images)"

# Download connector + driver JARs from Maven Central.
RUN mkdir -p /opt/flink/lib \
 && cd /opt/flink/lib \
 && curl -fsSL -o flink-sql-connector-kafka-${KAFKA_CONNECTOR}.jar \
    "https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/${KAFKA_CONNECTOR}/flink-sql-connector-kafka-${KAFKA_CONNECTOR}.jar" \
 && curl -fsSL -o flink-connector-jdbc-3.1.0-1.17.jar \
    "https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.0-1.17/flink-connector-jdbc-3.1.0-1.17.jar" \
 && curl -fsSL -o postgresql-${POSTGRES_DRIVER}.jar \
    "https://repo.maven.apache.org/maven2/org/postgresql/postgresql/${POSTGRES_DRIVER}/postgresql-${POSTGRES_DRIVER}.jar" \
 && ls -la /opt/flink/lib

USER flink