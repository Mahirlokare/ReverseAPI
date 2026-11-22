"""Passive security observations only; never sends probes or exploits."""
SENSITIVE_NAMES=("password","secret","token","authorization","api_key","apikey","cookie","session")
def lint_scan(scan):
    findings=[]
    for ep in scan.get("endpoints",[]):
        route=f"{ep.get('method','GET')} {ep.get('path','/')}"
        signals=ep.get("auth_signals",[])
        if not signals and ep.get("path") not in ("/","/health","/status"):
            findings.append({"severity":"info","rule":"AUTH_SIGNAL_NOT_OBSERVED","endpoint":route,"message":"No auth marker was observed in this capture; this does not prove the endpoint is unprotected."})
        if any(int(code)>=500 for code in ep.get("status_codes",[])):
            findings.append({"severity":"low","rule":"SERVER_ERROR_OBSERVED","endpoint":route,"message":"A 5xx response was observed in the provided traffic."})
        schema=ep.get("response_schema",{})
        properties=schema.get("properties",{}) if isinstance(schema,dict) else {}
        for name in properties:
            if any(word in name.lower() for word in SENSITIVE_NAMES):
                findings.append({"severity":"medium","rule":"SENSITIVE_FIELD_NAME","endpoint":route,"message":f"Response schema includes a sensitive-looking field name ({name}); confirm it is appropriately protected."})
    return findings
