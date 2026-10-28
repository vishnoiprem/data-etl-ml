from apache_beam.typehints.schemas import typing_to_runner_api

schema = typing_to_runner_api(Order)
print(schema)
