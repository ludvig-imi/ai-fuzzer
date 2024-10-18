# AI FUZZER

## IMPORTANT
This is only a POC. The final solution is supposed to run as a github action and automatically upload the templates to a centralized bucket (or similar)


## LLM Extraction
The LLM extraction is currently in `extractor.py`. It takes the relative path to services (which is input to the gh action) and iterates over all services one by one, and for each service finds all endpoints and extracts both schemas and views. It takes the raw code for the schemas + views and asks the LLM (claude in bedrock) to write an openapi spec, one for each view file and one for each schema.

## Parser
After the schema and view files has been extracted to openAPI spec we parse these files and creates input data templates which we then gives to our JSON fuzzer (JDAM), which in its turn create templates we can give to our actual fuzzing binary (ffuf).


## Files

* Fuzzing templates can be found in `fuzzing_templates`
* All openAPI JSON files can be found in `json`

## Test the parser
`pytest`


## Known problems
If JDAM is not running, make sure that you use the binary according to the architecture. Both arm and amd can be found in `.bin'. 