FROM python:3
EXPOSE 8000
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements.txt /code/
RUN pip install -r requirements.txt

ADD . /code/
RUN dir

CMD [ "python", "./manage.py", "runserver", "0.0.0.0:8000"]
