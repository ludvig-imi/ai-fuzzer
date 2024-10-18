from random import choice

class Parser:
    def __init__(self, schemas):
        self.schemas = schemas
        
        self.DEFAULT_VALUES = {
            "string": "fuzzstr",
            "integer": 0,
            "number": 0.0,
            "boolean": False,
            "date-time": "2024-10-14T00:00:00Z",
            "array": []
        }

    def _set_default_value(self, type):
        if type in self.DEFAULT_VALUES:
            return self.DEFAULT_VALUES[type]
        return None

    def _set_defaults(self, type, name):
        if "_date" in name:
            return self._set_default_value("date-time")
        elif "sitekey" in name:
            sitekey = "00000-00000-00000-00000"
            if type == "list" or type == "array":
                return [sitekey]
            else:
                return sitekey
        else:
            return self._set_default_value(type)


    def _parse_enum(self, enum, type):
        if type == "string":
            return choice(enum)
        elif type == "list" or type == "array":
            return [choice(enum)]

    def _parse_items(self, items):
        type = items.get("type", None)

        if type == "dict":
            return [
                self._parse_properties(items["properties"])
            ]

        else:
            return []

    """
        Properties is one or several objects
        {
            {
                "name": "test",
                "type": "string",
            },
            {
                "$ref": "test"
            }
        }
    """
    def _parse_properties(self, properties: dict) -> dict: 
        ret_props = {}

        for name, prop in properties.items():
            ref = prop.get("$ref", None)
            type = prop.get("type", None)
            enum = prop.get("enum", None)
            items = prop.get("items", None)

            if items and type == "list":
                ret_props[name] = self._parse_items(items)

            elif enum:
                ret_props[name] = self._parse_enum(enum, type)
                
            elif not ref:
                ret_props[name] = self._set_defaults(type, name)
            
            else:
                ref = ref.split("/")[-1]
                if ref in self.schemas:
                    ret_props[name] = self._parse_schema(self.schemas[ref])
    
        return ret_props
    
    """
        Schema:
        - type: object | string | integer
        - ref: {}
        - properties: {}
        - enum: {}
        - allOf: {}
    """
    def _parse_schema(self, schema):
        ref = schema.get("$ref", None)
        type = schema.get("type", None)
        properties = schema.get("properties", None)
        allOf = schema.get("allOf", None)
        
        # AllOf, concatination of schemas
        if allOf:
            sum_schemas = {}
            for sub_schema in allOf:
                sum_schemas |= self._parse_schema(sub_schema)

            return sum_schemas

        # Parse properties without fetching external schema
        elif not ref and properties:
            return self._parse_properties(properties)

        # Schema only has ref. Common case
        elif ref and not properties:
            ref = ref.split("/")[-1]
            if ref in self.schemas:
                return self._parse_schema(self.schemas[ref])

    """
    Parameters:
    - name: query
    - in: body
    - schema: {}
    """
    def _parse_parameters(self, parameters):
        parsed_params = {}
        for parameter in parameters:
            name = parameter.get("name", "")
            in_ = parameter.get("in", "")
            schema = parameter.get("schema", {})
            
            # Only consider body for now
            if in_ == "body":
                # Edge case where schema has no ref or properties
                if not schema.get("$ref", None) and not schema.get("properties", None):
                    parsed_params[name] = self._set_default_value(schema.get("type", None))
                else:
                    parsed_params = self._parse_schema(schema)
                
        return parsed_params

    def parse_openapi_v2(self, openapi_spec):
        parsed_schema = {}
        endpoints = openapi_spec.get("paths", {})
        for path in endpoints:
            parsed_schema[path] = {}
            for method in endpoints[path]:
                parsed_schema[path][method] = {}
                parameters = endpoints[path][method].get("parameters", [])
                parsed_schema[path][method] = self._parse_parameters(parameters)

        return parsed_schema