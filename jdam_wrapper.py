import subprocess
import os
import json

def run_jdam_binary(input_data):
    # Run JDAM binary with the input data
    jdam_path = "./.bin/jdam-arm64"
    jdam_mutators = "001,002,003,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022"
    count = 1
    cmd = f"echo '{input_data}' | {jdam_path} -mutators {jdam_mutators} -count {count}"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.wait()
    output = process.stdout.read().decode('utf-8')
    return output

def jdam_wrapper(input_data, output_dir):
    for service, apps in input_data.items():
        for app, parsed_spec in apps.items():
            for path, template in parsed_spec.items():
                for method, fuzz_template in template.items():
                    # TODO: Add fuzzing if query parameters are present

                    # Run the template through JDAM
                    fuzzed_data = run_jdam_binary(json.dumps(fuzz_template))
                    # Save the fuzzed data to a file according to the format
                    data_to_write = f"path:{path}\nmethod: {method}\n------\n{fuzzed_data}"""
                    fuzz_output_file = path.replace("/", "_")[1:]
                    
                    # Make sure the output directory exists                        
                    file_path = f"{output_dir}/{service}/{app}/{fuzz_output_file}.fuzz"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    # Write the fuzzed data to the file
                    open(file_path, "w").write(data_to_write)