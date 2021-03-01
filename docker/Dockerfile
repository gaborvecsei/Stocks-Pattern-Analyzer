FROM python:3.9.2-slim

RUN apt-get update

WORKDIR /code

COPY ./ /code/

RUN pip install -r requirements.txt

CMD ["/bin/bash", "/code/start.sh"]
