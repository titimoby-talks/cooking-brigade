from cooking_crew import CookingCrew


def main():
    example_query = "Menu italien pour 4 personnes, budget 150€, occasion anniversaire"
    # crew_output = CookingCrew().execute(example_query)
    #
    # # Accessing the crew output
    # print(f"Raw Output: {crew_output.raw}")
    # if crew_output.json_dict:
    #     print(f"JSON Output: {json.dumps(crew_output.json_dict, indent=2)}")
    # if crew_output.pydantic:
    #     print(f"Pydantic Output: {crew_output.pydantic}")
    # print(f"Tasks Output: {crew_output.tasks_output}")
    # print(f"Token Usage: {crew_output.token_usage}")
    CookingCrew().crew().kickoff(inputs={"user_query": example_query})


if __name__ == "__main__":
    main()
