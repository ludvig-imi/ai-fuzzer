from parser import Parser

test_schemas = {
    "testItem": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string"
            },
        }
    },
    "testItemMultiple": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string"
            },
            "id": {
                "type": "integer"
            }
        }
    },
    "testItemEnum": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "enum": ["myEnum"]
            },
        }
    },
    "testItemWithListProp": {
        "type": "object",
        "properties": {
            "myList": {
                "type": "list",
                "items": {
                    "type": "dict",
                    "properties": {
                        "param": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    },
    "testItemWithAllOf": {
        "allOf": [
            {
                "$ref": "#/test/testItem"
            },
            {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    }
                }
            }
        ]
    }
}

def run_parser_test(input_data, expected_output):
    parser = Parser(test_schemas)
    parsed_schema = parser.parse_openapi_v2(input_data)
    assert parsed_schema == expected_output

def test_schema_props_no_refs():
    input_data = {
        "paths": {
            "/my/path": {
                "post": {
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    expected_output = {
        "/my/path": {
            "post": {"name": "fuzzstr"}
        }
    }
    run_parser_test(input_data, expected_output)

def test_multiple_props_no_refs():
    input_data = {
        "paths": {
            "/my/path": {
                "post": {
                    "parameters": [
                        {
                            "name": "param",
                            "in": "body",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    },
                                    "id": {
                                        "type": "integer"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    expected_output = {
        "/my/path": {
            "post": {"name": "fuzzstr", "id": 0}
        }
    }
    run_parser_test(input_data, expected_output)

def test_schema_with_ref():
    input_data = {
        "paths": {
            "/my/path": {
                "post": {
                    "parameters": [
                        {
                            "name": "payload",
                            "in": "body",
                            "schema": {
                                "$ref": "#/test/testItem"
                            }
                        }
                    ]
                }
            }
        }
    }
    expected_output = {
        "/my/path": {
            "post": {"param": "fuzzstr"}
        }
    }
    run_parser_test(input_data, expected_output)

def test_schema_with_multiple_ref():
    input_data = {
        "paths": {
            "/my/path": {
                "post": {
                    "parameters": [
                        {
                            "name": "payload",
                            "in": "body",
                            "schema": {
                                "$ref": "#/test/testItemMultiple"
                            }
                        }
                    ]
                }
            }
        }
    }
    expected_output = {
        "/my/path": {
            "post": {"param": "fuzzstr", "id": 0}
        }
    }
    run_parser_test(input_data, expected_output)

def test_multiple_params_mix_ref_props():
    input_data = {
            "paths": {
                "/my/path": {
                    "post": {
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string"
                                        },
                                        "id": {
                                            "type": "integer"
                                        },
                                        "testitem": {
                                            "$ref": "#/test/testItem"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
    }
            
    expected_output =  {
        "/my/path": {
            "post": {"name": "fuzzstr", "id": 0, "testitem": {"param": "fuzzstr"}}    
        }
    }

    run_parser_test(input_data, expected_output)

def test_ref_with_enum():
    input_data = {
                "paths": {
                    "/my/path": {
                        "post": {
                            "parameters": [
                                {
                                    "name": "body",
                                    "in": "body",
                                    "schema": {
                                        "$ref": "#/test/testItemEnum"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
    expected_output = {
        "/my/path": {
            "post": {"param": "myEnum"}    
        }
    }
    run_parser_test(input_data, expected_output)

def test_ref_with_list_props():
    input_data = {
                "paths": {
                    "/my/path": {
                        "post": {
                            "parameters": [
                                {
                                    "name": "body",
                                    "in": "body",
                                    "schema": {
                                        "$ref": "#/test/testItemWithListProp"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
    expected_output = {
        "/my/path": {
            "post": {"myList": [{"param": "fuzzstr"}]}    
        }
    }
    run_parser_test(input_data, expected_output)

def test_ref_with_allof():
    input_data = {
                "paths": {
                    "/my/path": {
                        "post": {
                            "parameters": [
                                {
                                    "name": "body",
                                    "in": "body",
                                    "schema": {
                                        "$ref": "#/test/testItemWithAllOf"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
    expected_output = {
        "/my/path": {
            "post": {"param": "fuzzstr", "id": 0}    
        }
    }
    run_parser_test(input_data, expected_output)

def test_edge_case_schema_no_props_or_refs():
    input_data = {
        "paths": {
            "/my/path": {
                "post": {
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    expected_output = {
        "/my/path": {
            "post": {"name": "fuzzstr"}
        }
    }
    run_parser_test(input_data, expected_output)