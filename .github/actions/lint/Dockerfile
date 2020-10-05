FROM python:3.8

RUN pip install flake8-black

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

CMD [ "" ]
