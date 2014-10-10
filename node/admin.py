from django.contrib import admin
from django import forms

from node.models import NodeType, Node, Project, Corpus, Document



class NodeAdmin(admin.ModelAdmin):
    exclude = ('user', 'type', 'path', 'depth', 'numchild')
    list_display = ('name', 'date', 'file')
    search_fields = ('name',)
    # list_filter = ('type',)
    # date_hierarchy
    # inlines = [CorpusInLine,]

    #_nodetype_name = 'Project'
    #_parent_nodetype_name = 'Root'

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(NodeAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.user.id:
            return False
        return True

    def get_queryset(self, request):
        nodeType = NodeType.objects.get(name=self._nodetype_name)
        
        if request.user.is_superuser:
            #return Node.objects.all()
            return Node.objects.filter(type=nodeType)
        
        return Node.objects.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            nodeType        = NodeType.objects.get(name=self._nodetype_name)
            nodeTypeParent  = NodeType.objects.get(name=self._parent_nodetype_name)
            
            try:
                if nodeType.name == 'Project':
                    nodeParent  = Node.objects.get(type = nodeTypeParent, user = request.user)
                else:
                    nodeParent  = Node.objects.get(id = request.POST['parent'])
            except:
                nodeParent  = Node.add_root(type = nodeTypeParent, user = request.user, name="Parent")
            obj.user        = request.user
            
            node            = nodeParent.add_child(type = nodeType,\
                                                user    = request.user,\
                                                name    = obj.name,\
                                                file    = obj.file,\
                                                metadata= obj.metadata)
            
            #nodeParent.save()
            #node.save()
            obj = node
            
        else:
            obj.save()

class ProjectAdmin(NodeAdmin):
    _parent_nodetype_name   = 'Root'
    _nodetype_name          = 'Project'

class CorpusForm(forms.ModelForm):
    parent = forms.ModelChoiceField(Node.objects.filter(user_id=1, type_id=2))

class CorpusAdmin(NodeAdmin):
    _parent_nodetype_name = 'Project'
    _nodetype_name = 'Corpus'
    form = CorpusForm

class DocumentAdmin(NodeAdmin):
    _parent_nodetype_name = 'Corpus'
    _nodetype_name = 'Document'


admin.site.register(NodeType)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document, DocumentAdmin)


