from restful_checker.core.analyzer import analyze_api
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: restful-checker <path_to_openapi.json>")
    else:
        output = analyze_api(sys.argv[1])
        print(f"✅ Report generated: {output}")

if __name__ == "__main__":
    main()