FROM python:3.12.2 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./database_backend/api /app/api
COPY ./database_backend/config /app/config
COPY ./database_backend/manage.py /app/manage.py
COPY ./database_backend/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install -r requirements.txt


# Expose the port on which the server will run
EXPOSE 8000
EXPOSE 5432

COPY ./docker/database_backend/entrypoint.sh /app

RUN ls && chmod +x ./entrypoint.sh

# Run entrypoint script
CMD ["/bin/bash", "./entrypoint.sh"]