# -*- coding: utf-8 -*-
import grok
from zope.intid.interfaces import IIntIds
from zope.interface import Interface
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.app.container.interfaces import IContainer
from zope.traversing.browser.absoluteurl import absoluteURL
from hurry.jquery import jquery
from megrok import resource
from dolmen.app import security
from dolmen.app.layout import Top
from zope.security.management import checkPermission


class JSonNavTree(resource.ResourceLibrary):
    grok.name("menhir.simple.navtree")
    resource.path('resources')
    resource.resource('jquery.treeview.pack.js', depends=[jquery])
    resource.resource('jquery.treeview.async.js', depends=[jquery])
    resource.resource('navtree.css')


class NavTree(grok.Viewlet):
    grok.context(Interface)
    grok.viewletmanager(Top)

    def render(self):
        JSonNavTree.need()
        return """
        <script type="text/javascript">
        $(document).ready(function(){
	$(".treeview").treeview({
		url: "%s/@@navtreequery",
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
            name = getattr(child, 'title', child.__name__)
            
            entry = {
                "text": "<a href='%s'>%s</a>" % (url, name),
                "id": self.intid.queryId(child),
                "expanded": expanded,
                }

            if expanded and subentries:
                entry['children'] = self._buildTree(child)
            else:
                entry['hasChildren'] = subentries
            children.append(entry)
        return children
    
    def _buildTreeWithRoot(self, node):
        return [{
            "text":"<a href='%s'>%s</a>" % (absoluteURL(node, self.request), getattr(node, 'title')),
            "id":self.intid.queryId(self.context),
            "expanded":True,
            "children":self._buildTree(node)
        }]
                    

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
        if (root == u"source" or not root) and checkPermission(grok.name.bind().get(security.CanAddContent), self.context):
            # if we look at the site root, add in a root node which allows us to return to the site root/index easily
            return self._buildTreeWithRoot(node)
        else:
            return self._buildTree(node)
