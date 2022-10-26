import argparse
import os
import sys

# If we are running from a wheel, add the wheel to sys.path
# This allows the usage python pip-*.whl/pip install pip-*.whl
import unittest
import warnings

if __package__ == "":
    # __file__ is pip-*.whl/pip/__main__.py
    # first dirname call strips of '/__main__.py', second strips off '/pip'
    # Resulting path is the name of the wheel itself
    # Add that to sys.path so we can import pip
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

if __name__ == "__main__":
    # Work around the error reported in #9540, pending a proper fix.
    # Note: It is essential the warning filter is set *before* importing
    #       pip, as the deprecation happens at import time, not runtime.
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module=".*packaging\\.version"
    )


    parser = argparse.ArgumentParser(description="Converter: From/To Binary Templates")
    parser.add_argument('-i', "--input", dest="input",
                        help="Inputgrammarfile: File")
    parser.add_argument('-o', "--output", dest="output",
                        help="Outputgrammarfile: File")
    parser.add_argument('-u', "--other_files_which_annoy_me_atm", action='store_true',
                        help="Converts to other_files_which_annoy_me_atm, if not set it will convert from other_files_which_annoy_me_atm to binary template.")
    parser.add_argument('-r', "--rq", dest="rq", help="Specifies the RQ (use number)")

    pargs = parser.parse_args()
    if pargs.rq:
        if int(pargs.rq) == 1:
            from BTMeetsCFG.evaluation.RQ1 import main as _main
            sys.argv = sys.argv[0:1]
        elif int(pargs.rq) == 2:
            from BTMeetsCFG.evaluation.RQ2 import main as _main
        elif int(pargs.rq) == 3:
            from BTMeetsCFG.evaluation.RQ3 import main as _main
            sys.argv = sys.argv[0:1]
        elif int(pargs.rq) == 4:
            from BTMeetsCFG.evaluation.RQ4 import main as _main
        else:
            print(f"RQ{pargs.rq} not found!")
            sys.exit(-1)

        sys.exit(_main())
    else:
        from BTMeetsCFG.converter.convert import main as _main
        sys.exit(_main(pargs))
