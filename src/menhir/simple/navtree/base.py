# -*- coding: utf-8 -*-

import grok
import zope.app.intid
import megrok.resourcelibrary
from zope.app.intid import IIntIds
from zope.interface import Interface
from zope.component import getUtility
from zope.app.component.hooks import getSite
from zope.app.container.interfaces import IContainer
from zope.traversing.browser.absoluteurl import absoluteURL
from dolmen.app.layout.master import DolmenTop
from menhir.library.jquery import JQueryBase


class JSonNavTree(megrok.resourcelibrary.ResourceLibrary):
    grok.name("menhir.simple.navtree")
    megrok.resourcelibrary.depend(JQueryBase)
    megrok.resourcelibrary.directory('resources')
    megrok.resourcelibrary.include('jquery.treeview.pack.js')
    megrok.resourcelibrary.include('jquery.treeview.async.js')
    megrok.resourcelibrary.include('navtree.css')


class NavTree(grok.Viewlet):
    grok.context(Interface)
    grok.viewletmanager(DolmenTop)

    def render(self):
        JSonNavTree.need()
        return """
        <script type="text/javascript">
        $(document).ready(function(){
	$(".treeview").treeview({
		url: "%s/navtreequery",
                })
        });
        </script>
	<div class="navtree">
          <ul class="treeview treeview-gray">
          </ul>
        </div>""" % absoluteURL(self.context, self.request)


class JSONNavtreeQuery(grok.JSON):
    grok.context(Interface)

    def _buildTree(self, node):
        children = []
        for child in node.values():
            subentries = False
            if IContainer.providedBy(child):
                subentries = bool(len(child))
           
            url = absoluteURL(child, self.request)
            expanded = self.current.startswith(url)
            entry = {
                "text": "<a href='%s'>%s</a>" % (url, child.title),
                "id": self.intid.queryId(child),
                "expanded": expanded,
                }

            if expanded and subentries:
                entry['children'] = self._buildTree(child)
            else:
                entry['hasChildren'] = subentries
            children.append(entry)
        return children

    def navtreequery(self):
        self.intid = getUtility(IIntIds)
        self.current = absoluteURL(self.context, self.request)
        root = self.request.form.get('root')
        if root == u"source" or not root:
            node = getSite()
        else:
            node = self.intid.queryObject(int(root))
            if not node:
                raise NotImplementedError("Unexisiting node.")
        return self._buildTree(node)
