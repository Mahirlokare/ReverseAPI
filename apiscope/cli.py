"""APIScope command line interface."""
import argparse,json
from pathlib import Path
from apiscope.core.mvp_analysis import parse_har,summarize,export_openapi
def main():
    parser=argparse.ArgumentParser(prog="apiscope",description="Passive API inventory from authorized captures")
    sub=parser.add_subparsers(dest="command",required=True)
    har=sub.add_parser("har",help="Analyze a HAR file");har.add_argument("file");har.add_argument("--output",default="-")
    exp=sub.add_parser("openapi",help="Export OpenAPI from a previously generated scan JSON");exp.add_argument("scan");exp.add_argument("--output",default="openapi.json")
    args=parser.parse_args()
    if args.command=="har":
        scan=summarize(parse_har(json.loads(Path(args.file).read_text())))
        output=json.dumps(scan,indent=2)
    else:
        output=json.dumps(export_openapi(json.loads(Path(args.scan).read_text())),indent=2)
    if args.output=="-":print(output)
    else:Path(args.output).write_text(output);print(f"Written: {args.output}")
if __name__=="__main__":main()
