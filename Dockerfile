FROM conda/miniconda3


LABEL build="tornado-env" date="2018-04-16"
USER root
RUN  apt-get update && apt install libgl1-mesa-glx --yes && apt-get install gcc --yes

RUN conda install -y taxcalc=0.18.0 dask=0.17.2 distributed=1.21.6 tornado=5.0.1 bokeh>=0.12.3 -c ospc -c anaconda
RUN pip install gunicorn requests aiohttp aioredis pytest
