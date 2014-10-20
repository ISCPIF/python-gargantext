from django.contrib import admin
from django.forms import ModelForm, ModelChoiceField

from node.models import NodeType, Language, Node, Project, Corpus, Document

class NodeAdmin(admin.ModelAdmin):
    exclude = ('user', 'path', 'depth', 'numchild')
    list_display = ('name', 'date')
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
                    nodeParent  = Node.objects.create(id = request.POST['parent'])
            except:
                nodeParent  = Node.objects.create(type = nodeTypeParent, user = request.user, name=request.user.username)
            obj.user        = request.user
            
            node            = Node.objects.create(type = nodeType,\
                                                parent  = nodeParent,\
                                                user    = request.user,\
                                                name    = obj.name,\
                                                metadata= obj.metadata)
            
            #nodeParent.save()
            #node.save()
            obj = node
            
        else:
            obj.save()

######################################################################

class ProjectAdmin(NodeAdmin):
    _parent_nodetype_name   = 'Root'
    _nodetype_name          = 'Project'

######################################################################

from django.db.models.query import EmptyQuerySet

class CorpusForm(ModelForm):
    parent = ModelChoiceField(EmptyQuerySet)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CorpusForm, self).__init__(*args, **kwargs)
        parent_type = NodeType.objects.get(name="Project")
        #parent_type = NodeType.objects.get(name=self._parent_nodetype_name)
        self.fields['parent'].queryset = Node.objects.filter(user_id=self.request.user.id, type_id=parent_type.id)
    
    
    #self.parent = ModelChoiceField(Node.objects.filter(user_id=self.request.user.id, type_id=2))
    #parent = ModelChoiceField(Node.objects.filter(user_id=request.user.id, type_id=2))
    #print(self.request.user.id)
    class Meta:
        model = Corpus

class CorpusAdmin(NodeAdmin):
    _parent_nodetype_name = 'Project'
    _nodetype_name = 'Corpus'
    form = CorpusForm

######################################################################

class DocumentForm(ModelForm):
    parent = ModelChoiceField(Node.objects.filter(user_id=1, type_id=3))

class DocumentAdmin(NodeAdmin):
    _parent_nodetype_name = 'Corpus'
    _nodetype_name = 'Document'
    form = DocumentForm

class LanguageAdmin(admin.ModelAdmin):
    
    def get_queryset(self, request):
        return Language.objects.filter(implemented=1)
    
    class Meta:
        ordering = ['fullname',]


admin.site.register(NodeType)
admin.site.register(Language, LanguageAdmin)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document, DocumentAdmin)


