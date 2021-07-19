FROM dannyandersen/airflow-rpi:1.10.1

EXPOSE 8080

RUN mkdir -p /data/lib \
    && ln -s /data/lib/hadoop-3.3.0 /data/hadoop \
    && ln -s /data/lib/spark-3.0.1-bin-hadoop3.2 /data/spark \
    && apt update \
    && apt upgrade -y \
    && apt install -y libxml2-dev libxslt1-dev libopenblas-dev gfortran \
        python3-sklearn python3-sklearn-lib locales \
    && pip install wheel yfinance numpy sklearn bs4 hdfs tabulate dropbox httplib2 html5lib

ENTRYPOINT []
