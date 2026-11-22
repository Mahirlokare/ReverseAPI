"""APK static-analysis adapter using locally installed JADX; never launches APK."""
import shutil,subprocess,tempfile
from pathlib import Path
def analyze_apk(path,max_seconds=90):
    tool=shutil.which("jadx")
    if not tool: raise RuntimeError("JADX CLI not found. Install jadx and ensure jadx is on PATH.")
    apk=Path(path)
    if not apk.is_file() or apk.suffix.lower()!=".apk": raise ValueError("Input must be an APK file")
    with tempfile.TemporaryDirectory(prefix="apiscope-jadx-") as tmp:
        result=subprocess.run([tool,"-d",tmp,"--no-res","--show-bad-code",str(apk)],capture_output=True,text=True,timeout=max_seconds)
        if result.returncode: raise RuntimeError(result.stderr[-1500:] or "JADX failed")
        hits=[]
        import re
        route=re.compile(r"""["'](/(?:api|v[0-9]+|graphql|auth|users|orders|products)[^"'\s]*)["']""",re.I)
        for source in Path(tmp).rglob("*.java"):
            try:text=source.read_text(errors="replace")
            except OSError:continue
            for match in route.finditer(text):
                hits.append({"route":match.group(1),"source_file":source.name,"evidence":"string literal"})
        uniq={ (x["route"],x["source_file"]):x for x in hits}
        return {"files_analyzed":sum(1 for _ in Path(tmp).rglob("*.java")),"route_candidates":list(uniq.values()),"note":"Static string candidates only; no APK execution or active testing."}
