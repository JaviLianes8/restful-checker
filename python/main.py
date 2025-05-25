from core.analyzer import analyze_api
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_openapi.json>")
    else:
        output = analyze_api(sys.argv[1])
        print(f"✅ Report generated: {output}")