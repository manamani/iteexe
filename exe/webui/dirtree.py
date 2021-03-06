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

import sys
import logging
from exe.webui.renderable import RenderableResource
from twisted.web.resource import Resource
from exe.engine.path import Path
from urllib import unquote
import json
import mimetypes

log = logging.getLogger(__name__)

def get_drives():
    import string
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter + ":")
        bitmask >>= 1

    return drives

class DirTreePage(RenderableResource):
    name = "dirtree"
    
    def getChild(self, path, request):
        if path == "":
            return self
        return Resource.getChild(self, path, request)
    
    def render(self, request):
        if "sendWhat" in request.args:
            if request.args['sendWhat'][0] == 'dirs':
                pathdir = Path(request.args['node'][0])
                l = []
                try:
                    if pathdir == '/' and sys.platform[:3] == "win":
                        for d in get_drives():
                            l.append({ "text": d, "id": d + '\\'})
                    else:
                        for d in pathdir.dirs():
                            if not d.name.startswith('.') or sys.platform[:3] == "win":
                                l.append({ "text": d.name, "id": d.abspath() })
                except:
                    pass
            elif request.args['sendWhat'][0] == 'both':
                pathdir = Path(unquote(request.args['dir'][0]))
                items = []
                if pathdir == '/' and sys.platform[:3] == "win":
                    for d in get_drives():
                        items.append({ "name": d, "realname": d + '\\', "size": 0, "type": 'directory', "modified": 0})
                else:
                    parent = pathdir.parent
                    if (parent == pathdir):
                        realname = '/'
                    else:
                        realname = parent.abspath()
                    items.append({ "name": '..', "realname": realname, "size": parent.size, "type": "directory", "modified": int(parent.mtime), "perms": parent.lstat().st_mode })
                    try:
                        for d in pathdir.listdir():
                            if not d.name.startswith('.') or sys.platform[:3] == "win":
                                if d.isdir():
                                    pathtype = "directory"
                                elif d.isfile():
                                    pathtype = repr(mimetypes.guess_type(d.name, False)[0])
                                elif d.islink():
                                    pathtype = "link"
                                else:
                                    pathtype = "None"
                                items.append({ "name": d.name, "realname": d.abspath(), "size": d.size, "type": pathtype, "modified": int(d.mtime), "perms": d.lstat().st_mode })
                    except:
                        pass
                l = {"totalCount": len(items), 'results': len(items), 'items': items}
            return json.dumps(l).encode('utf-8')
        elif "query" in request.args:
            query = request.args['query'][0]
            pathdir = Path(unquote(request.args['dir'][0]))
            items = []
            if pathdir == '/' and sys.platform[:3] == "win":
                for d in get_drives():
                    items.append({ "name": d, "realname": d + '\\', "size": 0, "type": 'directory', "modified": 0})
            else:
                parent = pathdir.parent
                if (parent == pathdir):
                    realname = '/'
                else:
                    realname = parent.abspath()
                items.append({ "name": '..', "realname": realname, "size": parent.size, "type": "directory", "modified": int(parent.mtime), "perms": parent.lstat().st_mode })
                for d in pathdir.listdir():
                    if d.isdir():
                        pathtype = "directory"
                    elif d.isfile():
                        pathtype = repr(mimetypes.guess_type(d.name, False)[0])
                    elif d.islink():
                        pathtype = "link"
                    else:
                        pathtype = "None"
                    if d.name.startswith(query):
                        items.append({ "name": d.name, "realname": d.abspath(), "size": d.size, "type": pathtype, "modified": int(d.mtime), "perms": d.lstat().st_mode })
            l = {"totalCount": len(items), 'results': len(items), 'items': items}
            return json.dumps(l).encode('utf-8')
        return ""