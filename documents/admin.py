from django.contrib import admin

# Register your models here.
from nested_inlines.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from documents.models import Source, Language,\
        Project, Corpus, Document,\
        Ngram, NgramDocument, List, ListNgram,\
        Coocurrence, Clique, Phylo

from sources import importateur

class DocumentInLine(admin.StackedInline):
    model = Document
    extra = 0

class CorpusInLine(admin.StackedInline):
    model = Corpus
    extra = 0
    inlines = [DocumentInLine,]

class ProjectAdmin(admin.ModelAdmin):
    exclude = ('user',)
    list_display = ('title', 'date', 'user')
    inlines = [CorpusInLine,]

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(ProjectAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.user.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Project.objects.all()
        
        return Project.objects.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

class CorpusAdmin(admin.ModelAdmin):
    exclude = ('user',)
    list_display = ('title', 'date', 'database')
    #inlines = [DocumentInLine,]

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(CorpusAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.user.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Corpus.objects.all()
        
        return Corpus.objects.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()
        try:
            importateur.importer(obj.database, obj.language, obj.zip_file, project=obj.project, corpus=obj, user=obj.user)
            #importateur.importer(obj)
        except Exception as e:
            print("Error importateur", e)

class DocumentAdmin(admin.ModelAdmin):
    exclude         = ('user',)
    list_display    = ('date', 'source', 'title')
    list_per_page   = 20
    list_filter     = ('project', 'corpus')
    search_fields   = ('title',)

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(DocumentAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.user.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Document.objects.all()
        
        return Document.objects.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

class NgramAdmin(admin.ModelAdmin):
    list_display = ('terms', 'stem', 'n')
    list_per_page = 20

class NgramDocAdmin(admin.ModelAdmin):
    list_display = ('terms', 'document', 'occurrences')
    list_per_page = 20

class ListNgramAdmin(admin.ModelAdmin):
    list_display = ('mainForm', 'liste', 'cvalue')
    list_per_page = 20


admin.site.register(Source)
admin.site.register(Language)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document, DocumentAdmin)

admin.site.register(Ngram,NgramAdmin)
admin.site.register(NgramDocument, NgramDocAdmin)

admin.site.register(List)
admin.site.register(ListNgram, ListNgramAdmin)

admin.site.register(Coocurrence)
admin.site.register(Clique)
admin.site.register(Phylo)

