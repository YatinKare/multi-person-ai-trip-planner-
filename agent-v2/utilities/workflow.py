def get_instruction(prompt_name: str) -> str:
    with open(f"prompts/{prompt_name}", "r") as f:
        return f.read()