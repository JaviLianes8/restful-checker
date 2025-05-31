def show_help():
    """Show the help information for restful-checker."""
    help_text = """
    Basic usage of restful-checker:

    restful-checker <file.json|file.yaml|file.yml> [--format html|json|both]

    - Checks the RESTful best practices compliance of the API described by the OpenAPI file.
    - Generates a report in the specified format (default is HTML).

    Examples:
    restful-checker C:/path/to/api.yaml
    restful-checker C:/path/to/api.json --format both
    restful-checker https://example.com/openapi.json --format json

    You can also run it as a module:
    python -m restful_checker C:/path/to/api.yaml --format html
    """
    print(help_text)