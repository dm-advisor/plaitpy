import json
import argparse

parser = argparse.ArgumentParser(
    description="A program to prettify JSON. Provide full input JSON fie path as a command line argument."
)
parser.add_argument("input_file_path", help="Full file path of the JSON input file", type=str)

args = parser.parse_args()
input_filepath = args.input_file_path

with open(input_filepath, "r") as f:
    json_object = list(map(json.loads, f))

print(json.dumps(json_object, indent=1))
