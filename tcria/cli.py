from __future__ import annotations
import argparse, subprocess, sys, pathlib

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tcria", description="TCRIA — Legal evidence governance scanner (gateway audit).")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan a folder and generate audit outputs (json/md/pdf)")
    scan.add_argument("input", help="Folder to scan (e.g., ~/Downloads)")
    scan.add_argument("-o", "--out", default="output/audit", help="Output directory (default: output/audit)")
    scan.add_argument("--strict", action="store_true", help="Use strict-explicit-decision-record mode")
    scan.add_argument("--script", default="audit_accusation_bundle_with_tcr_gateway.py",
                      help="Path to the existing audit script (default: repo root)")
    scan.add_argument("--python", default=sys.executable, help="Python interpreter to run the script")

    args = p.parse_args(argv)

    if args.cmd == "scan":
        in_path = str(pathlib.Path(args.input).expanduser())
        out_dir = pathlib.Path(args.out).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [args.python, args.script, in_path, str(out_dir)]
        if args.strict:
            cmd.append("--strict")

        # NOTE: This delegates to your existing repo script; keep behavior centralized.
        print("Running:", " ".join(cmd))
        try:
            r = subprocess.run(cmd, check=False)
            return int(r.returncode or 0)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            print("Tip: run from the repo root, or pass --script path/to/audit_accusation_bundle_with_tcr_gateway.py")
            return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
