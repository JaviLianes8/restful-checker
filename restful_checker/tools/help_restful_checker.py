def show_help():
    """Show the help information for restful-checker."""
    help_text = """
    Basic usage of restful-checker:

    restful-checker <file.json|file.yaml|file.yml>
    - Checks the RESTful best practices compliance of the API described by the OpenAPI file.

    Example:
    restful-checker C:/path/to/*.json

    You can also use a URL instead of a file:
    restful-checker https://url/to/*.json
    """
    print(help_text)