#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
WALOUS_OCS_OBIA - Copyright (C) <2020> <Service Public de Wallonie (SWP), Belgique,
					          		Institut Scientifique de Service Public (ISSeP), Belgique,
									Université catholique de Louvain (UCLouvain), Belgique,
									Université Libre de Bruxelles (ULB), Belgique>
						 							
	
List of the contributors to the development of WALOUS_OCS_OBIA: see LICENSE file.
Description and complete License: see LICENSE file.
	
This program (WALOUS_OCS_OBIA) is free software: 
you can redistribute it and/or modify it under the terms of the 
GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) 
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (see COPYING file).  If not, 
see <http://www.gnu.org/licenses/>.
"""

import os, time, sys, math
import grass.script as gscript
from grass.pygrass.modules.grid.grid import GridModule

QUIET=True

def fill_band(bandmap, tilemask):
    '''Function to fill null pixels with interpolated values'''

    temporary_band = gscript.tempname(20)
    temporary_band2 = gscript.tempname(20)
    gscript.run_command('r.fill.stats',
                        flags='k',
                        input_=bandmap,
                        output=temporary_band,
                        distance=1,
                        cells=2,
                        overwrite=True,
                        quiet=QUIET)

    null_test = gscript.read_command('r.stats',
                                     flags='N',
                                     input_=[tilemask,temporary_band],
                                     quiet=QUIET).splitlines()

    while '1 *' in null_test:
        gscript.run_command('r.fill.stats',
                            flags='k',
                            input_=temporary_band,
                            output=temporary_band2,
                            distance=1,
                            cells=2,
                            overwrite=True,
                            quiet=QUIET)

        gscript.run_command('g.rename',
                            raster=[temporary_band2, temporary_band],
                            overwrite=True,
                            quiet=QUIET)

        null_test = gscript.read_command('r.stats',
                                         flags='N',
                                         input_=[tilemask,temporary_band],
                                         quiet=QUIET).splitlines()

    filled_band = "%s_filled" % bandmap
    mapcalc_expression = "%s = round(%s)" % (filled_band, temporary_band)
    gscript.run_command('r.mapcalc',
                        expression=mapcalc_expression,
                        quiet=QUIET)


    gscript.run_command('g.remove',
                        type='raster',
                        name=temporary_band,
                        flags='f',
                        quiet=QUIET)

    return filled_band


def tile_size(PROCESSES):
    region_info = gscript.region()
    x_cells = region_info['e']-region_info['w']
    y_cells = region_info['n']-region_info['s']
    y_x_ratio = float(y_cells)/float(x_cells)
    x_tilenumber = math.sqrt(float(PROCESSES) / float(y_x_ratio))
    y_tilenumber = y_x_ratio * x_tilenumber
    x_tile_size = int(round(float(x_cells) / x_tilenumber))
    y_tile_size = int(round(float(y_cells) / y_tilenumber))

    return x_tile_size, y_tile_size


def calculate_panvis(BANDS, x_tile_size, y_tile_size, PROCESSES, TUILE):

    panvis_map = 'walous_temppanvis_%i_%i' % (TUILE, os.getpid())
    mapcalc_expression = "%s = round((%s + %s + %s) / 3.0)" % (panvis_map,
                                                               BANDS['red'],
                                                               BANDS['green'],
                                                               BANDS['blue'])

    gscript.run_command('r.mapcalc.tiled',
                        expression=mapcalc_expression,
                        tile_width=x_tile_size,
                        tile_height=y_tile_size,
                        overlap=0,
                        processes=PROCESSES,
                        mapset_prefix='rmapcalc_%i' % TUILE,
                        quiet=QUIET)

    return panvis_map
