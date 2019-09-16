#!/usr/bin/env python3
import itertools
import fileinput
from pathlib import Path

import numpy as np
import ninja_syntax


outdir = Path("test_pictures")
for d in [outdir]:
    d.mkdir(exist_ok=True)

ninjafile = Path("build.ninja")
n = ninja_syntax.Writer(ninjafile.open('w', encoding='utf-8'))

n.variable('FFMPEG', "/usr/local/bin/ffmpeg -y -threads 0")


n.rule(
    name='defisheye',
    command='''\
$FFMPEG -i $in \
-vf "lenscorrection=cx=0.5:cy=0.5:k1=$k1:k2=$k2" \
$out\
'''
)

infile = Path("./base.jpg")
for k1 in np.linspace(-1,1,21):
    for k2 in np.linspace(-0.1,0.1,21):
        outfile = outdir / Path(f"{infile.stem}_{k1}_{k2}.jpg")
        var = {'k1': str(k1), 'k2': str(k2)}
        n.build(
            rule="defisheye",
            outputs=str(outfile),
            inputs=str(infile),
            variables=var
        )

n.close()
print("Generated build.ninja! Now run ninja.")


