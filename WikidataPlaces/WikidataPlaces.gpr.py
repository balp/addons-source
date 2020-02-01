#  Copyright (C) 2020.  Anders Arnholm <Anders@Arnholm.se>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

# File: HelloWorld.gpr.py
register(GRAMPLET,
         id="WikidataPlaces World Gramplet",
         name=_("WikidataPlaces World Gramplet"),
         description = _("a program that says 'Hello World'"),
         status = STABLE,
         version="0.0.1",
         fname="WikidataPlaces.py",
         height = 180,
         gramplet = 'WikidataPlacesGramplet',
         gramplet_title=_("WikidataPlaces Gramplet"),
         gramps_target_version="5.1",
         help_url="WikidataPlaces Gramplet"
         )