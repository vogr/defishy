#!/usr/bin/env python3
import itertools
from pathlib import Path

import ninja_syntax

"""
Currently there are color issues when applying the `lenscorrection` filter
or the `vidstabtransform` filter to videos encoded in yuv422p. A (hopefully)
temporary fix used in this script is to upsample the videos to yuv444p before
applying the script, and then to downsample them back to yuv422p:

* input video -> yuv444p -> filter -> yuv420p -> output video

"""


intermediate_lenscorrect_dir = Path("intermediate_lenscorrect")
stabfiles_dir = Path("stab_files")
outdir = Path("processed_dnxhr")

class Builder():
    def __init__(self, ninjaname='build.ninja'):
        self.ninjafile = Path(ninjaname)
        print(f"Ninjafile will be \"{self.ninjafile}\"")

        # Truncate ninjafile
        self.ninjafile.write_text("")

        for d in [intermediate_lenscorrect_dir, stabfiles_dir, outdir]:
            d.mkdir(exist_ok=True)

    def __enter__(self):
        # Context manager object can be reused: if this is the case
        # we will append the new commands to the file.
        self.n = ninja_syntax.Writer(self.ninjafile.open('a', encoding='utf-8'))

        self.n.variable('FFMPEG', "ffmpeg -y -threads 0")

        # !!!!! The order is important !!!! You should lenscorrect BEFORE applying
        # video stabilization, as lenscorrect uses the center of the image as a reference,
        # and vidstab moves things around.

        FMT422 = "format=yuv422p"
        FMT444 = "format=yuv444p"

        LENSCORRECT = 'lenscorrection=cx=0.5:cy=0.5:k1=-0.227:k2=0.045'

        LENSCORRECT_FILTER = ','.join([FMT444, LENSCORRECT, FMT422])
        self.n.rule(
            name='lenscorrect',
            command=(
                '$FFMPEG $pre_args '
                '-i $in '
                f'-filter:v {LENSCORRECT_FILTER} '
                '-c:a copy '
                '-c:v dnxhd -profile:v dnxhr_sq '
                '$out'
            )
        )

        # "Note the use of the ffmpeg's unsharp filter which is always
        # recommended." (https://github.com/georgmartius/vid.stab)
        VIDSTAB_DETECT = "vidstabdetect=result=$out"
        VIDSTAB_TRANSFORM = 'vidstabtransform=input="$in_stab"'
        UNSHARP = 'unsharp=5:5:0.8:3:3:0.4'

        PASS1_FILTER = ','.join([FMT444, VIDSTAB_DETECT])
        PASS2_FILTER = ','.join([FMT444, VIDSTAB_TRANSFORM, UNSHARP,FMT422])
        self.n.rule(
            name='vidstab-pass1',
            command=(
                '$FFMPEG $pre_args '
                '-i $in '
                f'-filter:v  {PASS1_FILTER} '
                '-f null -'
            )
        ) # out must be a .trf file
        self.n.rule(
            name='vidstab-pass2',
            command=(
                '$FFMPEG $pre_args '
                '-i $infile '
                f'-filter:v {PASS2_FILTER} '
                '-c:a copy '
                '-c:v dnxhd -profile:v dnxhr_sq '
                '$out'
            )
        )
        # A note on dnxhr: `-c:v dnxhd profile:v dnxhr_sq` is equivalent to `-c:v dnxhd -b:v 145M`
        # but is framerate and resolution independant
        # /!\ with profile dnxhr_sd, the format is necessarily yuv422p.
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.n.close()
        if exc_type:
            print(f'exc_type: {exc_type}')
            print(f'exc_value: {exc_value}')
            print(f'exc_traceback: {exc_traceback}')


    def defishy_stabilize(self, in_name, pre_args=None):
        infile = Path(in_name)
        lenscorrected = (intermediate_lenscorrect_dir / infile).with_suffix('.d.mov')
        stabfile = (stabfiles_dir / infile).with_suffix('.d.trf')
        outfile = (outdir / infile).with_suffix('.ds.mov')
        self.n.build(
            rule="lenscorrect",
            outputs=str(lenscorrected),
            inputs=str(infile),
            variables={'pre_args': pre_args}
        )
        self.n.build(
            rule="vidstab-pass1",
            outputs=str(stabfile),
            inputs=str(lenscorrected),
            variables={} # Intermediate file is already cut as required!
        )
        self.n.build(
            rule="vidstab-pass2",
            outputs=str(outfile),
            inputs=[str(lenscorrected), str(stabfile)],
            variables={'infile': str(lenscorrected), 'in_stab': str(stabfile)}
        )

    def defishy(self, in_name, pre_args=None):
        infile = Path(in_name)
        outfile = (outdir / infile).with_suffix('.d.mov')
        self.n.build(
            rule="lenscorrect",
            outputs=str(outfile),
            inputs=str(infile),
            variables={'pre_args': pre_args}
        )

    def stabilize(self, in_name, pre_args=None):
        infile = Path(in_name)
        stabfile = (stabfiles_dir / infile).with_suffix('.trf')
        outfile = (outdir / infile).with_suffix('.s.mov')
        self.n.build(
            rule="vidstab-pass1",
            outputs=str(stabfile),
            inputs=str(infile),
            variables={'pre_args': pre_args}
        )
        self.n.build(
            rule="vidstab-pass2",
            outputs=str(outfile),
            inputs=[str(infile), str(stabfile)],
            variables={'pre_args': pre_args, 'infile': str(infile), 'in_stab': str(stabfile)}
        )

