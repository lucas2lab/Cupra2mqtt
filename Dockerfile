FROM python:3-alpine

WORKDIR /code
RUN mkdir -p /code/WeConnect-Cupra-python

COPY WeConnect-Cupra-python/image_extra_requirements.txt ./
RUN pip install --no-cache-dir -r image_extra_requirements.txt

COPY WeConnect-Cupra-python ./WeConnect-Cupra-python
RUN cd WeConnect-Cupra-python &&\
python3 -m pip install --upgrade build &&\
python3 -m build --sdist &&\
python3 -m build --wheel &&\
pip install .

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src ./src

CMD [ "python", "src/main.py" ]