# core/rest_docs.py

REST_BEST_PRACTICES = {
    "versioning": {
        "title": "API Versioning",
        "type": "warning",
        "link": "https://restfulapi.net/versioning/",
        "summary": "Use /v1/ in the routes to ensure backward compatibility."
    },
    "naming": {
        "title": "Resource Naming",
        "type": "warning",
        "link": "https://restfulapi.net/resource-naming/",
        "summary": "Avoid verbs in URIs and prefer plural nouns for collections."
    },
    "http_methods": {
        "title": "HTTP Method Semantics",
        "type": "warning",
        "link": "https://restfulapi.net/http-methods/",
        "summary": "Use HTTP methods according to REST conventions: GET for retrieval, POST for creation, DELETE for deletion, etc."
    },
    "status_codes": {
        "title": "Status Codes",
        "type": "warning",
        "link": "https://restfulapi.net/http-status-codes/",
        "summary": "Define standard status codes for each HTTP method. Avoid default-only responses."
    },
    "param_consistency": {
        "title": "Parameter Naming Consistency",
        "type": "warning",
        "link": "https://restfulapi.net/resource-naming/",
        "summary": "Use consistent naming for path parameters across endpoints."
    },
    "query_filters": {
        "title": "Collection Filtering",
        "type": "warning",
        "link": "https://spec.openapis.org/oas/v3.1.0#parameter-object",
        "summary": "Collection resources should support query filtering using ?key=value."
    }
}

def linkify(msg, key):
    link = REST_BEST_PRACTICES[key]['link']
    return f'{msg} <a href="{link}" target="_blank">More info</a>'
