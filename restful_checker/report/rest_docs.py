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
    },
    "SSL": {
        "title": "Use HTTPS",
        "type": "error",
        "link": "https://restfulapi.net/security-essentials/",
        "summary": "All APIs should be served over HTTPS to ensure secure communication."
    },
    "ContentType": {
        "title": "Use JSON",
        "type": "error",
        "link": "https://restfulapi.net/json-rest-api/",
        "summary": "Use application/json for request and response content where possible. Avoid XML unless necessary."
    },
    "resource_nesting": {
        "title": "Resource Nesting",
        "type": "warning",
        "link": "https://restfulapi.net/resource-naming/",
        "summary": "Nesting should include parent resource IDs when appropriate (e.g., /users/{id}/orders)."
    },
    "ResponseExamples": {
        "title": "Response Examples",
        "type": "warning",
        "link": "https://spec.openapis.org/oas/v3.0.3#response-object",
        "summary": "Use 'example' or 'examples' in response bodies to improve clarity and documentation."
    },
    "error_format": {
        "title": "Consistent Error Format",
        "type": "warning",
        "link": "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#error-handling",
        "summary": "Error responses should include fields like 'code' and 'message' in a structured format."
    },
    "Pagination": {
        "title": "Pagination Support",
        "type": "warning",
        "link": "https://jsonapi.org/format/#fetching-pagination",
        "summary": "GET endpoints for collections should support pagination parameters like `page` and `limit`."
    }
}

def linkify(msg, key):
    link = REST_BEST_PRACTICES[key]['link']
    return f'{msg} <a href="{link}" target="_blank">More info</a>'
