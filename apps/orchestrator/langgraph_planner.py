def generate_plan(objective: str):
    plan_markdown = f"""
# Plan for: {objective}

Based on the objective, we will perform the following steps:
1. Analyze the repository structure.
2. Implement the requested changes in the codebase.
3. Verify the changes and generate a patch.
4. Generate any requested artifacts (like documentation or reports).
    """

    tasks = [
        {
            "title": "Analyze and Prepare",
            "description": f"Analyze the repo for objective: {objective}",
            "order_index": 0
        },
        {
            "title": "Implement Changes",
            "description": f"Execute the main logic for: {objective}",
            "order_index": 1
        }
    ]

    if "xlsx" in objective.lower() or "planilha" in objective.lower():
        tasks.append({
            "title": "Generate Report (xlsx)",
            "description": "Create a spreadsheet with the summary of actions.",
            "order_index": 2
        })

    return plan_markdown, tasks
