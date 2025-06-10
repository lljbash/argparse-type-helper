import argparse
import sys
from typing import Never

from targs import Flag, Name, extract_targs, register_targs, targ, targs


@targs
class MyArgs:
    input_file: str = targ(Name)
    """The input file to process."""
    iter: int = targ(Flag, default=10, help="Number of items to process.")
    debug: bool = targ(Flag("-d"), action="store_true", help="Enable debug mode.")
    extra: list[str] = targ(
        ("-e", "--extra"),
        action="extend",
        nargs="+",
        default=[],
        help="Extra arguments.",
    )
    """Extra arguments to pass to the processing function."""


class MyParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


if __name__ == "__main__":
    parser = MyParser(description="Process some data arguments.")
    register_targs(parser, MyArgs, verbose=True)
    args = parser.parse_args()
    my_args = extract_targs(args, MyArgs)
    print(f"Parsed arguments: {my_args}")
