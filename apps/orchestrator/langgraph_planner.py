import uuid

def generate_plan(objective: str):
    """
    Simulated ChatDev multi-agent workflow.
    Agents: CEO, CTO, Programmer, Reviewer.
    """

    # Simulate a conversation log for the UI
    chat_log = [
        "CEO: We need to start a new project for: " + objective,
        "CTO: Understood. I will design the architecture and break it down into tasks.",
        "Programmer: I'm ready to implement the features once the plan is ready.",
        "Reviewer: I will ensure the code quality and generate the final patch."
    ]

    plan_markdown = f"""
# ChatDev Multi-Agent Plan
**Objective:** {objective}

## Agent Discussion
- **CEO**: Initiated the project.
- **CTO**: Designed the module structure.
- **Programmer**: Assigned to core implementation.
- **Reviewer**: Assigned to verify changes and generate diff.

## Execution Steps
1. **Analysis Phase**: Understanding the requirements and existing codebase.
2. **Coding Phase**: Implementing the logic.
3. **Review Phase**: Finalizing the patch and artifacts.
    """

    tasks = [
        {
            "title": "[CTO] Architecture Design",
            "description": f"Identify the files and structures needed for: {objective}",
            "order_index": 0
        },
        {
            "title": "[Programmer] Core Implementation",
            "description": f"Execute the main coding tasks for: {objective}",
            "order_index": 1
        },
        {
            "title": "[Reviewer] Quality Assurance & Patching",
            "description": "Verify the implementation and produce the final git patch.",
            "order_index": 2
        }
    ]

    if "xlsx" in objective.lower() or "planilha" in objective.lower():
        tasks.append({
            "title": "[CPO] Artifact Generation (XLSX)",
            "description": "Generate the requested spreadsheet report.",
            "order_index": 3
        })

    return plan_markdown, tasks, chat_log
