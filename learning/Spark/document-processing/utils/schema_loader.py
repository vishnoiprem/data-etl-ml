# utils/schema_loader.py
import json
from typing import Dict, Any
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, FloatType, BooleanType, \
    TimestampType, DateType, ArrayType, MapType, BinaryType


class SchemaLoader:
    """Loads and parses JSON schemas into Spark StructTypes"""

    @staticmethod
    def load_schema(file_path: str) -> Dict[str, Any]:
        """Load schema from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def create_spark_schema(schema_def: Dict[str, Any]) -> StructType:
        """Convert JSON schema definition to Spark StructType"""
        columns = []

        for column_def in schema_def.get('columns', []):
            spark_type = SchemaLoader._map_type(column_def['type'])
            field = StructField(
                name=column_def['name'],
                dataType=spark_type,
                nullable=column_def.get('nullable', True)
            )
            columns.append(field)

        return StructType(columns)

    @staticmethod
    def _map_type(type_str: str):
        """Map JSON schema type string to Spark DataType"""
        type_mapping = {
            'string': StringType(),
            'integer': IntegerType(),
            'int': IntegerType(),
            'long': LongType(),
            'float': FloatType(),
            'double': FloatType(),
            'boolean': BooleanType(),
            'timestamp': TimestampType(),
            'date': DateType(),
            'binary': BinaryType()
        }

        # Handle complex types
        if type_str.startswith('array<'):
            # Extract inner type
            inner_type_str = type_str[6:-1]  # Remove 'array<' and '>'
            inner_type = SchemaLoader._map_type(inner_type_str)
            return ArrayType(inner_type)

        elif type_str.startswith('struct<'):
            # Extract struct fields
            fields_str = type_str[7:-1]  # Remove 'struct<' and '>'
            fields = []
            for field_def in fields_str.split(','):
                field_name, field_type = field_def.split(':', 1)
                fields.append(StructField(field_name.strip(), SchemaLoader._map_type(field_type.strip())))
            return StructType(fields)

        elif type_str.startswith('map<'):
            # Extract key and value types
            types_str = type_str[4:-1]  # Remove 'map<' and '>'
            key_type_str, value_type_str = types_str.split(',', 1)
            key_type = SchemaLoader._map_type(key_type_str.strip())
            value_type = SchemaLoader._map_type(value_type_str.strip())
            return MapType(key_type, value_type)

        # Return basic type or default to StringType
        return type_mapping.get(type_str.lower(), StringType())