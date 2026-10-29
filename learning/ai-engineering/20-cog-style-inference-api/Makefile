.PHONY: up api test smoke

up:
\tpip install -r requirements.txt

api:
\tuvicorn api.server:app --reload --port 8091

test:
\tpytest -q

smoke:
\tpython -c "from api.predict import predict, PredictInput; print(predict(PredictInput(prompt='test')))"
\tpython -m api.billing
