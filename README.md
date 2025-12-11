## Init project
### Prepare db:
``
docker-compose up -d
``

``
uv run init_db.py
``

## Backend
### Run server:
``uv run uvicorn main:app --reload``

## Frontend
### Run server:
``uv run streamlit run ui.py``

