"""Audit exact centered observations without a supplied scene or camera poses.

Input JSON is {"Y": [[rational, ...], ...]} in consecutive two-row view blocks.
Rationals are integers or strings such as "2/3". No approximate rank test is used.
"""

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from exact import mat, encode
from produce import data_only
from check import check_data_only


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.input.stat().st_size>8*1024*1024:
            raise ValueError('this command accepts at most 8 MiB of JSON')
        raw=json.loads(args.input.read_text())['Y']
        if not isinstance(raw,list) or not raw or len(raw)>1024:
            raise ValueError('supply 1 to 512 two-row view blocks')
        if any(not isinstance(r,list) or not r or len(r)>4096 for r in raw):
            raise ValueError('supply between 1 and 4096 points')
        if any(type(x) not in (str,int) for r in raw for x in r):
            raise ValueError('coordinates must be integer values or rational strings, not floats')
        y=mat(raw)
        if any(max(x.numerator.bit_length(),x.denominator.bit_length())>256 for r in y for x in r):
            raise ValueError('coordinate numerator and denominator must each fit in 256 bits')
        record=encode(data_only(y))
        check_data_only(record)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps({'accepted':True,'scene_recovers_width_four':record['scene_recovers_width_four'],
                          'universal_classification':record['width_four_classification']['classification']},indent=2))
    except (KeyError,TypeError,ValueError,IndexError,OSError) as exc:
        raise SystemExit('REJECT: '+str(exc))


if __name__=='__main__':
    main()
