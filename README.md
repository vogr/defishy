# Defishy

> /!\ Due to a bug in FFmpeg, this script currently has major drawbacks: since it needs to upsample then downsample the pixel format (yuv420 -> yuv444 -> yuv422), colors aren't preserved as well as they should be.


Defishy uses [vid.stab](https://github.com/georgmartius/vid.stab) and [FFmpeg](https://ffmpeg.org/) to both stabilize videos shot with a GoPro Hero 3, and remove the fish-eye effect. [Ninja](https://ninja-build.org/) is used as a build tool to paralellize the calls to ffmpeg.

Defishy is a Python library providing a context manager. With this infrastructure, it's super easy to describe what you want:
```python3
#!/usr/bin/env python3
from defishy import Builder

with Builder() as b:
    b.stabilize("GOPR0037.MP4")
    b.stabilize("GOPR0038.MP4", "-t 00:12")
    b.lenscorrect("GOPR0047.MP4", "-ss 00:10")
``

The previous Python script will generate a `build.ninja`file. You may analyze its content, and then run `ninja` to process the videos. They will end up in the `processed_dnxhr` directory.

* "GOPR0037.MP4" will be stabilized and defisheyed
* the first 12s of "GOPR0038.MP4" will be stabilized and defisheyed
* "GOPR0047.MP4" wlll only be defisheyed, and only the part after 10s will be kept

## Installation and prerequisites

You need a build of FFmpeg with `libvidstab` intagretion. The easiest route is to download a build from [John Van Sockle's website](https://johnvansickle.com/ffmpeg/), to extract it, and to put the executable in your path (e.g. put `ffmpeg` in `/usr/local/bin`).

You will also need the [Ninja build system](https://ninja-build.org/):
```
sudo apt install ninja-build
```

You may then install defishy as a Python module:
```console
git clone "https://gitlab.com/vogier/defishy"
cd defishy/
python3 -m pip install --user .
```


## Technical details

Defishy uses FFmpeg's [`lenscorrection`](https://ffmpeg.org/ffmpeg-filters.html#lenscorrection) filter to remove the fish-eye distorsion. This filter takes two parameters: `k1` and `k2`. The scripts in `research/` were used to find the optimal `k1` and `k2` parameters. The `genhtml` script gives you the opportunity to view all the generated images arranged in lines and columns corresponding to the values of `k1` and `k2`: simply open the generated html file in your browser to view the image grid.

Ultimately, for my GoPro 3 Silver Edition:

* `k1 = -0.227` was given [here](https://stackoverflow.com/questions/30832248/is-there-a-way-to-remove-gopro-fisheye-using-ffmpeg/40659507) using an exact calculation.
* `k2 = 0.045` was found by generating all the images corresponding to `k1=-0.227` and `k2` taking its values [-0.1..0.1] with increments of 0.01.
