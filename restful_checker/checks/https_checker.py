from restful_checker.checks.check_result import CheckResult

def check_https_usage(openapi_data):
    result = CheckResult("SSL")
    servers = openapi_data.get("servers", [])

    if not servers:
        result.warning("No servers defined in OpenAPI spec")
    else:
        all_https = all(s.get("url", "").startswith("https://") for s in servers)
        if not all_https:
            result.error("Not all servers use HTTPS")
        else:
            result.success("All servers use HTTPS")

    return result.messages, result.finalize_score()