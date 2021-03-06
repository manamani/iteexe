# -- coding: utf-8 --
# ===========================================================================
# eXe 
# Copyright 2012, Pedro Peña Pérez, Open Phoenix IT
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# ===========================================================================

"""
StyleMenu provides a list of Styles used in eXe and handle related client events
"""

import logging
from exe.webui.renderable import Renderable
from twisted.web.resource import Resource
log = logging.getLogger(__name__)
import json

# ===========================================================================
class StyleMenu(Renderable, Resource):
    """
    StyleMenu provides a list of Styles used in eXe and handle related client events
    """
    name = 'styleMenu'

    def __init__(self, parent):
        """ 
        Initialize
        """ 
        Renderable.__init__(self, parent)
        if parent:
            self.parent.putChild(self.name, self)
        Resource.__init__(self)

    def process(self, request):
        log.debug("process")
        
        if ("action" in request.args and 
            request.args["action"][0] == "ChangeStyle"):
            log.debug("changing style to "+request.args["object"][0])
            self.package.style = request.args["object"][0]
            
            
    def render(self, request=None):
        """
        Returns a JSON string with the styles
        """
        log.debug("render")

        l = []
        printableStyles = [(x.capitalize(), x) for x in self.config.styles]
        for printableStyle, style in sorted(printableStyles, key=lambda x: x[0]):
            l.append({ "label": printableStyle, "style": style, "selected": True if style == self.package.style else False})
        return json.dumps(l).encode('utf-8')
        
    
# ===========================================================================
