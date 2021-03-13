FROM python:3.9.2-slim

RUN apt-get update

# Requirements copied first, not the whole project, so code change won't trigger a pip install always
# It is only triggered when the requirements.txt changes
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /code

ENTRYPOINT ["/bin/bash"]
