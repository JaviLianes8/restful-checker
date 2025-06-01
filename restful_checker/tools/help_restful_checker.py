def show_help():
    """Show the help information for restful-checker."""
    help_text = """
    Basic usage of restful-checker:

    restful-checker <file.json|file.yaml|file.yml> [--output-format html|json|both] [--output-folder ./route]

    - Checks the RESTful best practices compliance of the API described by the OpenAPI file.
    - Generates a report in the specified format (default is HTML).
    - Stores the output files in the specified folder (default is ./html).

    Examples:
    restful-checker C:/path/to/api.yaml
    restful-checker C:/path/to/api.json --output-format both
    restful-checker https://example.com/openapi.json --output-format json --output-folder reports

    You can also run it as a module:
    python -m restful_checker C:/path/to/api.yaml --output-format html --output-folder ./output
    """
    print(help_text)