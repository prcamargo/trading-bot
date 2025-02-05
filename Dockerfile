FROM python:3.13-slim

# Define variáveis de ambiente
ENV BINANCE_API_KEY=00000000 \
    BINANCE_API_SECRET=0000000 

# Install Poetry
RUN pip3 install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
# Install dependencies
RUN poetry install --no-root
COPY src /app/src

EXPOSE 8050

ENTRYPOINT ["poetry", "run", "python", "src/app.py"]