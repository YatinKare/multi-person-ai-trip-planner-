
import logging
import inspect
import sys
from google.adk.runners import Runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_class(cls):
    print(f"\nInspecting {cls.__name__}:")
    print("-" * 20)
    # Get all methods
    methods = [func for func in dir(cls) if callable(getattr(cls, func)) and not func.startswith("__")]
    for method in methods:
        print(f"Method: {method}")

    if hasattr(cls, "model_fields"):
        print("\nPydantic Fields:")
        for name, field in cls.model_fields.items():
            print(f"  - {name}: {field.annotation}")


    # Check for specific interesting methods like invoke, run, etc.
    for interesting in ["invoke", "run", "call", "execute", "run_async"]:
        if hasattr(cls, interesting):
            print(f"!!! Found '{interesting}' method !!!")
            try:
                sig = inspect.signature(getattr(cls, interesting))
                print(f"Signature: {sig}")
            except Exception as e:
                print(f"Could not get signature: {e}")
        else:
            print(f"Did not find '{interesting}' method")

try:
    inspect_class(Runner)
except ImportError as e:
    print(f"Error importing: {e}")
except Exception as e:
    print(f"Error: {e}")
