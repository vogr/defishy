#!/usr/bin/env python3

import numpy as np

html = ['<!DOCTYPE HTML>\n']

html.append('<head>')
html.append('<link rel="stylesheet" href="styles.css">')
html.append('</head>\n')

html.append('<body>')
for k1 in np.linspace(-1,1,21):
    html.append('<div>\n')
    for k2 in np.linspace(-0.1,0.1,21):
        html.append(f'<img src="test_pictures/base_{k1}_{k2}.jpg"></img>')
    html.append('</div>\n')
html.append('</body>\n')
print(''.join(html))
