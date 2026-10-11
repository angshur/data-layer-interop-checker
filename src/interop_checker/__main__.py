import json
import sys

from .analyze import analyze


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m interop_checker stack.json", file=sys.stderr)
        return 2
    try:
        result = analyze(json.load(open(argv[0])))
    except (ValueError, KeyError) as exc:
        print("invalid stack: %s" % exc, file=sys.stderr)
        return 2
    print("Identity Fragmentation Score: %d/100 (%s)" % (result["score"], result["label"]))
    for f in result["flags"]:
        print("  [%s] %s" % (f["level"], f["text"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
