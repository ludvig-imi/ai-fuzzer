import json
import ast
import os
import logging
import config
from helpers import (
    call_bedrock,
    create_runtime,
    read_file,
    strip_bedrock_output,
    add_openapi_spec_details,
    chunk_code
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

BEDROCK_RUNTIME = create_runtime()

def find_schemas_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

    imports_with_schemas = []

    # Find all imports that contain 'schemas'
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'schemas' in alias.name:
                    imports_with_schemas.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and 'schemas' in node.module:
                imports_with_schemas.append(node.module)

    # Convert from code import string to relative path
    relative_paths = []
    for imp in imports_with_schemas:
        relative_path = imp.replace('.', os.sep) + '.py'
        relative_paths.append(relative_path)

    return relative_paths

def call_bedrock_chunked(full_code, chunk_size, bedrock_runtime, system_instruction):
    code_chunks = chunk_code(full_code, chunk_size)
    responses = []
    for chunk in code_chunks:
        chunked_code = system_instruction + chunk
        response = call_bedrock(chunked_code, bedrock_runtime)

        # Make sure that the response is JSON objects that's comma separated
        # Find the first json object
        try:
            json.loads(response)
        except:
            # Remove all lines until we find line with ": {
            lines = response.split("\n")
            for idx, line in enumerate(lines):
                if "\": {" in line:
                    response = "\n".join(lines[idx:])
                    break
            
            if response.endswith("}"):
                response = response + ","
            
            # Strip LLM output
            response = response.replace("```", "")

        responses.append(response)
    
    combined_response = "\n".join(responses)
    return combined_response

def iterate_views_files(root_dir="."):
    import os
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith("views.py"):
                yield os.path.join(root, file)

def get_schema_paths(relative_schema_paths, relative_base, views_file):
    paths = []
    for relative_path in relative_schema_paths:
        if "/" not in relative_path:
            schema_dir = views_file.split("/")[:-1]
            paths.append('/'.join(schema_dir)+"/"+relative_path)
        else:
            paths.append(relative_base + "/" + relative_path)

    return paths

def get_schema_code(schema_paths, service):
    schema_code = []
    for schema_path in schema_paths:
        # Check if the schema already has been scanned
        scanned_schemas = open(f"./scanned_files/{service}.scanned_schemas", "r").read()
        if schema_path in scanned_schemas:
            continue
        try:
            code = read_file(schema_path)
            schema_code.append(code)
            with open(f"./scanned_files/{service}.scanned_schemas", "a") as f:
                f.write(schema_path + "\n")
        except Exception as e:
            pass
    
    return schema_code

def write_schema_json(schema_answer, service):
    # It should not be valid JSON
    try:
        json.loads(schema_answer)
        raise Exception("The schema answer should not be valid JSON")
    except:
        if not os.path.exists(f"./json/{service}.schemas.json"):
            pre_schema_file_data = "{"
            open(f"./json/{service}.schemas.json", "w").write(pre_schema_file_data)
        else:
            pre_schema_file_data = open(f"./json/schemas/{service}.schemas.json", "r").read()
            if pre_schema_file_data.endswith("}"):
                pre_schema_file_data = pre_schema_file_data[:-1] + ","
        

        # Patch schema answer
        if schema_answer.endswith(","):
            schema_answer = schema_answer[:-1]

        # Append the new schemas to the file
        write_data = pre_schema_file_data + schema_answer  + "}"

        if write_data.endswith("},}"):
            write_data = write_data[:-2] + "}"
        # make sure it's valid JSON
        try:
            json.loads(write_data)
        except:
            open("error.json", "w").write(write_data)
            raise Exception("The schema answer should be valid JSON")

        open(f"./json/{service}.schemas.json", "w").write(write_data)
        return


def get_schema_from_bedrock(schema_code, chunk_size=10000):
    schemas_code = "\n".join(schema_code)
    schema_answer = call_bedrock_chunked(schemas_code, chunk_size, BEDROCK_RUNTIME, config.system_instruction_schemas)
    return schema_answer

def write_views_file(bedrock_answer, service, package_dir):
    swagger_ui_json = {
        "openapi": "3.0.0",
        "definitions": {},
        "info": {
            "title": "Stats API",
            "version": "1.0.0"
        },
        "paths": {}
    }
        
    if "No endpoints found." in bedrock_answer:
        logger.debug("No endpoints found.")
    else:
        json_answer = strip_bedrock_output(bedrock_answer)
        openapi_spec = add_openapi_spec_details(json_answer)
        swagger_ui_json["paths"] = openapi_spec
        swagger_ui_json_file = f"{package_dir.split('/')[-1]}.views.json"
        open(f"./json/{service}"+swagger_ui_json_file, "w").write(json.dumps(swagger_ui_json, indent=4))


# The path to the exchange services... Of course temporary until merged with mono
def extractor(services_starting_point="../services"):
    services = os.listdir(services_starting_point)
    for service in services:
        service_dir = os.path.join(services_starting_point, service)
        files = list(iterate_views_files(service_dir))

        for views_file in files:
            package_dir = views_file.split("/")[-2]
            relative_schema_paths = find_schemas_imports(views_file)
            schema_paths = get_schema_paths(relative_schema_paths, service_dir, views_file)
            logger.debug(f"Found schema paths {schema_paths} for {service}")
            schema_code = get_schema_code(schema_paths, service)
            schema_answer = get_schema_from_bedrock(schema_code)
            write_schema_json(schema_answer, service)

            # Views file
            logger.debug(f"Calling claude for endpoints from {views_file}")
            code = read_file(views_file)
            answer = call_bedrock(config.system_instruction_endpoints+code, BEDROCK_RUNTIME)
            write_views_file(answer, service, package_dir)