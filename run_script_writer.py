import argparse
import os
import threading
from dotenv import load_dotenv
from huggingface_hub import login
from agents.script_writer import ScriptWriterAgent

# Load environment variables and login to Hugging Face
load_dotenv(override=True)
if os.getenv("HF_TOKEN"):
    login(os.getenv("HF_TOKEN"))

append_answer_lock = threading.Lock()

def parse_args():
    parser = argparse.ArgumentParser(description="Script Writer Agent with Deep Research")
    parser.add_argument(
        "prompt",
        type=str,
        help="Script writing prompt (e.g., 'Write a thriller set in 1920s Chicago')"
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="o1",
        help="Model ID to use (default: o1)"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maximum number of steps for the agent"
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        default=2,
        help="Verbosity level (0-3)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialize the agent
    agent = ScriptWriterAgent(
        model_id=args.model_id,
        max_steps=args.max_steps,
        verbosity_level=args.verbosity
    )
    
    # Run the script writing process
    script = agent.write_script(args.prompt)
    
    print("\nFinal Script:")
    print("=" * 80)
    print(script)
    print("=" * 80)

if __name__ == "__main__":
    main() 