def show_help():
    """
    Show usage examples and help for restful-checker CLI.
    """
    print("""
╔════════════════════════════════════════════════════════════════╗
║                       RESTFUL-CHECKER CLI                      ║
╚════════════════════════════════════════════════════════════════╝

Usage:
    restful-checker <file.json|file.yaml|file.yml> 
                    [--output-format html|json|both] 
                    [--output-folder ./route]

Description:
    - Checks RESTful best practices in an OpenAPI definition.
    - Generates reports in HTML or JSON format.
    - Outputs files to the specified folder (default is ./html).

Examples:
    restful-checker ./openapi.yaml
    restful-checker ./openapi.json --output-format both
    restful-checker https://example.com/openapi.json --output-format json --output-folder reports

As Python module:
    python -m restful_checker ./openapi.yaml 
              --output-format html 
              --output-folder ./output
""")