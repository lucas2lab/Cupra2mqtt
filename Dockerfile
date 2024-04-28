FROM python:3-alpine

WORKDIR /code
COPY WeConnect-Cupra-python ./WeConnect-Cupra-python

WORKDIR /code/WeConnect-Cupra-python

RUN pip install --no-cache-dir -r image_extra_requirements.txt
RUN python3 -m pip install --upgrade build
RUN python3 -m build --sdist
RUN python3 -m build --wheel
RUN pip install .

WORKDIR /code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

CMD [ "python", "src/main.py" ]