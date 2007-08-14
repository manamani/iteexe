# ===========================================================================
# eXe 
# Copyright 2004-2005, University of Auckland
# Copyright 2006-2007 eXe Project, New Zealand Tertiary Education Commission
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
Exports an eXe package as an IMS Content Package
"""

import logging
import re
from cgi                           import escape
from zipfile                       import ZipFile, ZIP_DEFLATED
from exe.webui                     import common
from exe.webui.blockfactory        import g_blockFactory
from exe.engine.error              import Error
from exe.engine.path               import Path, TempDirPath
from exe.export.pages              import Page, uniquifyNames
from exe.engine.uniqueidgenerator  import UniqueIdGenerator

log = logging.getLogger(__name__)


# ===========================================================================
class Manifest(object):
    """
    Represents an imsmanifest xml file
    """
    def __init__(self, config, outputDir, package, pages):
        """
        Initialize
        'outputDir' is the directory that we read the html from and also output
        the mainfest.xml 
        """
        self.config       = config
        self.outputDir    = outputDir
        self.package      = package
        self.idGenerator  = UniqueIdGenerator(package.name, config.exePath)
        self.pages        = pages
        self.itemStr      = ""
        self.resStr       = ""


    def save(self):
        """
        Save a imsmanifest file and metadata to self.outputDir
        """
        filename = "imsmanifest.xml"
        out = open(self.outputDir/filename, "wb")
        out.write(self.createXML().encode('utf8'))
        out.close()
        # if user did not supply metadata title, description or creator
        #  then use package title, description, or creator in imslrm
        #  if they did not supply a package title, use the package name
        lrm = self.package.dublinCore.__dict__.copy()
        if lrm.get('title', '') == '':
            lrm['title'] = self.package.title
        if lrm['title'] == '':
            lrm['title'] = self.package.name
        if lrm.get('description', '') == '':
            lrm['description'] = self.package.description
        if lrm['description'] == '':
            lrm['description'] = self.package.name
        if lrm.get('creator', '') == '':
            lrm['creator'] = self.package.author
        # Metadata
        templateFilename = self.config.xulDir/'templates'/'dublincore.xml'
        template = open(templateFilename, 'rb').read()
        xml = template % lrm
        out = open(self.outputDir/'dublincore.xml', 'wb')
        out.write(xml.encode('utf8'))
        out.close()

    def createXML(self):
        """
        returning XLM string for manifest file
        """
        manifestId = self.idGenerator.generate()
        orgId      = self.idGenerator.generate()
        
        xmlStr = u"""<?xml version="1.0" encoding="UTF-8"?>
        <!-- generated by eXe - http://exelearning.org -->
        <manifest identifier="%s" 
        xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
        xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2" 
        xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        """ % manifestId 

        xmlStr += "\n "
        xmlStr += "xsi:schemaLocation=\"http://www.imsglobal.org/xsd/"
        xmlStr += "imscp_v1p1 imscp_v1p1.xsd "        
        xmlStr += "http://www.imsglobal.org/xsd/imsmd_v1p2 imsmd_v1p2p2.xsd\""
        xmlStr += "> \n"
        xmlStr += "<metadata> \n"
        xmlStr += " <schema>IMS Content</schema> \n"
        xmlStr += " <schemaversion>1.1.3</schemaversion> \n"
        xmlStr += " <adlcp:location>dublincore.xml"
        xmlStr += "</adlcp:location> \n" 
        xmlStr += "</metadata> \n"
        xmlStr += "<organizations default=\""+orgId+"\">  \n"
        xmlStr += "<organization identifier=\""+orgId
        xmlStr += "\" structure=\"hierarchical\">  \n"

        if self.package.title != '':
            title = escape(self.package.title)
        else:
            title  = escape(self.package.root.titleShort)
        xmlStr += u"<title>"+title+"</title>\n"
        
        depth = 0
        for page in self.pages:
            while depth >= page.depth:
                self.itemStr += "</item>\n"
                depth -= 1
            self.genItemResStr(page)
            depth = page.depth

        while depth >= 1:
            self.itemStr += "</item>\n"
            depth -= 1

        xmlStr += self.itemStr
        xmlStr += "</organization>\n"
        xmlStr += "</organizations>\n"
        xmlStr += "<resources>\n"
        xmlStr += self.resStr
        xmlStr += "</resources>\n"
        xmlStr += "</manifest>\n"
        return xmlStr
        
            
    def genItemResStr(self, page):
        """
        Returning xml string for items and resources
        """
        itemId   = "ITEM-"+unicode(self.idGenerator.generate())
        resId    = "RES-"+unicode(self.idGenerator.generate())
        filename = page.name+".html"
            
        
        self.itemStr += "<item identifier=\""+itemId+"\" isvisible=\"true\" "
        self.itemStr += "identifierref=\""+resId+"\">\n"
        self.itemStr += "    <title>"
        self.itemStr += escape(page.node.titleShort)
        self.itemStr += "</title>\n"
        
        self.resStr += "<resource identifier=\""+resId+"\" "
        self.resStr += "type=\"webcontent\" "

        self.resStr += "href=\""+filename+"\"> \n"
        self.resStr += """\
    <file href="%s"/>
    <file href="base.css"/>
    <file href="content.css"/>""" % filename
        self.resStr += "\n"
        fileStr = ""

        for resource in page.node.getResources():
            fileStr += "    <file href=\""+escape(resource)+"\"/>\n"

        self.resStr += fileStr
        self.resStr += "</resource>\n"


# ===========================================================================
class IMSPage(Page):
    """
    This class transforms an eXe node into a SCO 
    """
    def save(self, outputDir):
        """
        This is the main function.  It will render the page and save it to a
        file.  
        'outputDir' is the name of the directory where the node will be saved to,
        the filename will be the 'self.node.id'.html or 'index.html' if
        self.node is the root node. 'outputDir' must be a 'Path' instance
        """
        out = open(outputDir/self.name+".html", "w")
        out.write(self.render())
        out.close()
        

    def render(self):
        """
        Returns an XHTML string rendering this page.
        """
        html  = common.docType()
        html += u"<html xmlns=\"http://www.w3.org/1999/xhtml\">\n"
        html += u"<head>\n"
        html += u"<meta http-equiv=\"Content-type\" content=\"text/html; "
        html += u" charset=utf-8\" />\n";
        html += u"<title>"+_("eXe")+"</title>\n"
        html += u"<style type=\"text/css\">\n"
        html += u"@import url(base.css);\n"
        html += u"@import url(content.css);\n"
        html += u"</style>\n"
        html += u'<script type="text/javascript" src="common.js"></script>\n'
        html += u"</head>\n"
        html += u"<body>\n"
        html += u"<div id=\"outer\">\n"
        html += u"<div id=\"main\">\n"
        html += u"<div id=\"nodeDecoration\">\n"
        html += u'<p id=\"nodeTitle\">\n'
        html += escape(self.node.titleLong)
        html += u'</p>\n'
        html += u"</div>\n"

        for idevice in self.node.idevices:
            block = g_blockFactory.createBlock(None, idevice)
            if not block:
                log.critical("Unable to render iDevice.")
                raise Error("Unable to render iDevice.")
            if hasattr(idevice, "isQuiz"):
                html += block.renderJavascriptForWeb()
            if idevice.title != "Forum Discussion":
                html += block.renderView(self.node.package.style)

        html += u"</div>\n"
        html += self.renderLicense()
        html += self.renderFooter()
        html += u"</div>\n"
        html += u"</body></html>\n"
        html = html.encode('utf8')
        return html


        
# ===========================================================================
class IMSExport(object):
    """
    Exports an eXe package as a SCORM package
    """
    def __init__(self, config, styleDir, filename):
        """ Initialize
        'styleDir' is the directory from which we will copy our style sheets
        (and some gifs)
        """
        self.config       = config
        self.imagesDir    = config.webDir/"images"
        self.scriptsDir   = config.webDir/"scripts"
        self.templatesDir = config.webDir/"templates"
        self.schemasDir   = config.webDir/"schemas/ims"
        self.styleDir     = Path(styleDir)
        self.filename     = Path(filename)
        self.pages        = []


    def export(self, package):
        """ 
        Export SCORM package
        """
        # First do the export to a temporary directory
        outputDir = TempDirPath()

        # Copy the style sheet files to the output dir
        # But not nav.css
        styleFiles  = [self.styleDir/'..'/'base.css']
        styleFiles += [self.styleDir/'..'/'popup_bg.gif']
        styleFiles += self.styleDir.files("*.css")
        if "nav.css" in styleFiles:
            styleFiles.remove("nav.css")
        styleFiles += self.styleDir.files("*.jpg")
        styleFiles += self.styleDir.files("*.gif")
        styleFiles += self.styleDir.files("*.png")
        styleFiles += self.styleDir.files("*.js")
        styleFiles += self.styleDir.files("*.html")
        self.styleDir.copylist(styleFiles, outputDir)

        # copy the package's resource files
        package.resourceDir.copyfiles(outputDir)
            
        # Export the package content
        self.pages = [ IMSPage("index", 1, package.root) ]

        self.generatePages(package.root, 2)
        uniquifyNames(self.pages)

        for page in self.pages:
            page.save(outputDir)

        # Create the manifest file
        manifest = Manifest(self.config, outputDir, package, self.pages)
        manifest.save()
        
        # Copy the scripts
        self.scriptsDir.copylist(('libot_drag.js',
                                  'common.js'), outputDir)
        
        self.schemasDir.copylist(('imscp_v1p1.xsd',
                                  'imsmd_v1p2p2.xsd',
                                  'ims_xml.xsd'), outputDir)
        
        # copy players for media idevices.                
        hasFlowplayer     = False
        hasMagnifier      = False
        hasXspfplayer     = False
        isBreak           = False
        
        for page in self.pages:
            if isBreak:
                break
            for idevice in page.node.idevices:
                if (hasFlowplayer and hasMagnifier and hasXspfplayer):
                    isBreak = True
                    break
                if not hasFlowplayer:
                    if 'flowPlayer.swf' in idevice.systemResources:
                        hasFlowplayer = True
                if not hasMagnifier:
                    if 'magnifier.swf' in idevice.systemResources:
                        hasMagnifier = True
                if not hasXspfplayer:
                    if 'xspf_player.swf' in idevice.systemResources:
                        hasXspfplayer = True
                        
        if hasFlowplayer:
            videofile = (self.templatesDir/'flowPlayer.swf')
            videofile.copyfile(outputDir/'flowPlayer.swf')
        if hasMagnifier:
            videofile = (self.templatesDir/'magnifier.swf')
            videofile.copyfile(outputDir/'magnifier.swf')
        if hasXspfplayer:
            videofile = (self.templatesDir/'xspf_player.swf')
            videofile.copyfile(outputDir/'xspf_player.swf')

        # Copy a copy of the GNU Free Documentation Licence
        (self.templatesDir/'fdl.html').copyfile(outputDir/'fdl.html')
        # Zip it up!
        self.filename.safeSave(self.doZip, _('EXPORT FAILED!\nLast succesful export is %s.'), outputDir)
        # Clean up the temporary dir
        outputDir.rmtree()

    def doZip(self, fileObj, outputDir):
        """
        Actually does the zipping of the file. Called by 'Path.safeSave'
        """
        zipped = ZipFile(fileObj, "w")
        for scormFile in outputDir.files():
            zipped.write(scormFile,
                    scormFile.basename().encode('utf8'), ZIP_DEFLATED)
        zipped.close()

    def generatePages(self, node, depth):
        """
        Recursive function for exporting a node.
        'outputDir' is the temporary directory that we are exporting to
        before creating zip file
        """
        for child in node.children:
            pageName = child.titleShort.lower().replace(" ", "_")
            pageName = re.sub(r"\W", "", pageName)
            if not pageName:
                pageName = "__"

            page = IMSPage(pageName, depth, child)

            self.pages.append(page)
            self.generatePages(child, depth + 1)
    
# ===========================================================================
