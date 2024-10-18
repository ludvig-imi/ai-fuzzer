import json
import os
from parser import Parser
from extractor import extractor
from jdam_wrapper import jdam_wrapper

def extract_from_LLM():
    extractor(services_starting_point="../services")

def parse_openapi_specs():
    prepared_data = []

    schema_files = os.listdir("./json/schemas")
    for schema in schema_files:
        service = schema.split(".")[0]
        
        prepared_service_data = {}
        prepared_service_data[service] = {}

        service_schemas = json.loads(open(f"./json/schemas/{service}.schemas.json", "r").read())
        parser = Parser(service_schemas)

        view_files = os.listdir(f"./json/views/{service}")
        for file in view_files:
            app = file.split(".")[0]
            openapi_spec = json.loads(open(f"./json/views/{service}/{app}.views.bedrock.json", "r").read())

            parsed_schema = parser.parse_openapi_v2(openapi_spec)
            prepared_service_data[service][app] = parsed_schema
            
    return prepared_service_data

if __name__ == "__main__":
    
    # Extract data from LLM
    # extract_from_LLM("../hmt-mono/services")

    # Then parse all the openapi specs
    prepared_data = parse_openapi_specs()

    # Create input to the fuzzer
    jdam_wrapper(prepared_data, "./fuzzing_templates")