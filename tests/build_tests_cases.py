import csv
import os
import sys
import readline

sys.path.append("../tupi")
import tupi
from tupi.noun import Noun

# Define file paths
source_file = "cases.csv"
new_cases_file = "new_cases.csv"


# Load CSV data into memory
def load_csv(file_path):
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


new_cases = []
command = ""
expected_result = ""

commands = ["exit", "save", "next", "set"]


# REPL function
def repl(data):
    global command, expected_result, new_cases
    for record in data:
        while True:
            verbete = record["verbete"]
            definition = record["raw_definition"]
            n = Noun(verbete, definition)
            scratch = Noun(verbete, definition)
            scratch_command = "n.verbete()"
            print(f"\nVerbete: {n.verbete()}\n")
            print(f"Raw Definition: {definition}\n\n")
            # ----------------------------------------------
            command = input("Enter command: ")
            if command.lower() in commands or command.startswith("n."):
                inp_cmd = command.lower()
                if inp_cmd == "exit":
                    print("Done! Exiting...")
                    # Store new test cases
                    store_new_cases(new_cases)
                    new_cases = []
                    del data[0]
                    command = ""
                    sys.exit(0)
                elif inp_cmd == "next":
                    print("Next verbete...")
                    break
                elif inp_cmd == "set":
                    expected_result = input("Enter expected result: ")
                    print(f"Expected Result set to: {expected_result}")
                    continue
                elif inp_cmd == "save":
                    print("Saving transform... Moving on...")
                    new_cases.append(
                        {
                            "verbete": verbete,
                            "definition": definition,
                            "expected_result": expected_result,
                            "transform": scratch_command,
                        }
                    )
                    continue
                elif command.startswith("n."):
                    try:
                        scratch = eval(command)
                        scratch_command = command
                        # Simulate modifying the text
                        print(f"Transformed Output: {scratch}")
                        print(f"Expected Output   : {expected_result}")
                        if scratch == expected_result:
                            print("Transform is valid! Saving...")
                            new_cases.append(
                                {
                                    "verbete": verbete,
                                    "definition": definition,
                                    "expected_result": expected_result,
                                    "transform": scratch_command,
                                }
                            )
                            continue
                    except Exception as e:
                        print(f"Not valid transform...{e}")
            else:
                print(
                    f"{command} is not a valid command. Please enter a valid command."
                )

        # while command.lower() != 'done':
        #     verbete = record['verbete']
        #     definition = record['raw_definition']
        #     n = Noun(verbete, definition)
        #     scratch = Noun(verbete, definition)
        #     scratch_command = 'n.verbete()'
        #     print(f"\nVerbete: {n.verbete()}\n")
        #     print(f"Raw Definition: {definition}\n\n")

        #     expected_result = input("Enter expected result: ")

        #     command = ''
        #     while command.lower() != 'done':
        #         command = input("Enter command to modify text (or 'done' to finish): ")
        #         if command.lower() != 'done':
        #             if command.lower() == "save":
        #                 print("Saving transform... Moving on...")
        #                 new_cases.append({
        #                     'verbete': verbete,
        #                     'definition': definition,
        #                     'expected_result': expected_result,
        #                     'transform': scratch_command
        #                 })
        #                 break
        #             try:
        #                 scratch = eval(command)
        #                 scratch_command = command
        #                 # Simulate modifying the text
        #                 print(f"Transform Output: {scratch}")
        #                 if scratch == expected_result:
        #                     print("Transform is valid! Moving on...")
        #                     new_cases.append({
        #                         'verbete': verbete,
        #                         'definition': definition,
        #                         'expected_result': expected_result,
        #                         'transform': scratch_command
        #                     })
        #                     break
        #             except Exception as e:
        #                 print("Not valid transform...")
        # # Store new test cases
        # store_new_cases(new_cases)
        # new_cases = []
        # del data[0]
        # command = ''


def store_new_cases(new_cases):
    file_exists = os.path.isfile(new_cases_file)
    with open(new_cases_file, mode="a", newline="", encoding="utf-8") as file:
        fieldnames = ["verbete", "definition", "expected_result", "transform"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for case in new_cases:
            writer.writerow(case)
    new_cases = []


if __name__ == "__main__":
    data = load_csv(source_file)
    while True:
        try:
            repl(data)
        except KeyboardInterrupt:
            print("\nCtrl+C detected! Reprompting...")
