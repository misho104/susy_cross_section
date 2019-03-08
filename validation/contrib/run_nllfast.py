#!env python3
"""A script to run NLLfast/NNLLfast and get their interpolation result."""

import configparser
import itertools
import logging
import pathlib
import re
import shlex
import subprocess
from typing import Any, Iterator, List, Sequence, Union

import click
import coloredlogs
import numpy

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PathLike = Union[str, pathlib.Path]


class Runner:
    """A program runner constructed from a configuration file."""

    program: str
    make_cmd: str
    data_dir: pathlib.Path

    config_files = ["run_nllfast.cfg", "run_nllfast.cfg.default"]  # type: List[str]

    def __init__(self, program, make_cmd="", data_dir="."):
        # type: (str, str, PathLike)->None
        self.program = program
        self.make_cmd = make_cmd
        self.data_dir = pathlib.Path(data_dir)

    def make(self, force=False):
        # type: (bool)->None
        """Compile the program from source codes."""
        prog_path = pathlib.Path(self.program)
        if prog_path.is_file() and not force:
            logger.info("Program exists; avoiding make.")
            return
        if not self.make_cmd:
            logger.critical("make_cmd not configured.")
            exit(1)
        logger.info("make %s: %s", self.program, self.make_cmd)
        ret = subprocess.run(
            shlex.split(self.make_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        for line in ret.stdout.decode().strip().splitlines():
            logger.info("STDOUT: %s", line)
        if ret.returncode != 0:
            logger.critical("Make failed.")
            for line in ret.stderr.decode().strip().splitlines():
                logger.info(f"STDERR: %s", line)
            exit(1)
        if not prog_path.is_file():
            logger.critical("make succeeded without generating program.")
            exit(1)

    def run_iter(self, *args):
        # type: (Any)->Iterator[str]
        """Run the program and yield each line."""
        cmd = [str(x) for x in [pathlib.Path(self.program).absolute(), *args]]
        working_dir = self.data_dir
        logger.info("dir: %s", working_dir)
        logger.info("RUN: %s", " ".join(cmd))
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=working_dir
        )
        while True:
            line = proc.stdout.readline().decode()
            yield line
            if not line and proc.poll() is not None:
                break

    def run(self, *args):
        # type: (Any)->None
        """Run the program and print the output."""
        for line in self.run_iter(*args):
            print(line, end="")

    @classmethod
    def from_config(cls, name):
        # type: (str)->Runner
        """Construct a runner from configuration file."""
        config = configparser.ConfigParser()
        for f in cls.config_files:
            config.read(f)
            if config.sections():
                break
        if name not in config.sections():
            logger.critical("Configuration not found for: %s", name)
            exit(1)

        data = {"program": config[name]["program"]}

        if "default" in config.sections():
            if "root_dir" in config["default"]:
                data["root_dir"] = config["default"]["root_dir"]
            if config["default"].get("guess_root_dir") == "git":
                c = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE
                )
                data["root_dir"] = c.stdout.decode().strip()

        def replace(text):
            try:
                return re.sub(r"\$\{(.*?)\}", lambda m: data[m.group(1)], text)
            except KeyError:
                logger.critical("Invalid variable is used: %s", text)
                exit(1)

        make_cmd = replace(config[name].get("make_cmd", ""))
        data_dir = replace(config[name].get("data_dir", ""))
        return cls(program=data["program"], make_cmd=make_cmd, data_dir=data_dir)

    @classmethod
    def args_iter(cls, *args):
        # type: (str)->Iterator[Sequence[str]]
        """Generate an interator using numpy.arange."""
        iterators = []
        for a in args:
            if ":" in a:
                s = [float(x) if "." in x else int(x) for x in a.split(":")]
                iterators.append(numpy.arange(*s))
            else:
                iterators.append([a])
        return itertools.product(*iterators)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("name", required=True)
@click.argument("args", nargs=-1)
@click.pass_context
def main(context, **kw):
    # type: (Any, Any)->None
    """Run NLLfast (or NNLLfast) to get their interpolation result.

    This program loads the configurations from "run_nllfast.cfg" if exists, or
    otherwise from "run_nllfast.cfg.default", which are Python Config files.

    NAME is a table name specified in the configuration.

    The arguments, ARGS, are directly passed to the program except that
    variables separated by ":" are interpreted as ranges (with the same format
    as Python's range class, and iteration over the ranges are performed.
    """
    r = Runner.from_config(kw["name"])
    r.make()
    for args in r.args_iter(*kw["args"]):
        for line in r.run_iter(*args):
            if line.startswith("  "):
                line = re.sub(r"  +", "\t", line.strip())
                print(line)
            else:
                logger.info(line.strip())


if __name__ == "__main__":
    coloredlogs.install(
        level=logging.INFO, logger=logging.getLogger(), fmt="%(levelname)8s %(message)s"
    )
    main()
