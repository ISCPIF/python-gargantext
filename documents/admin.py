from django.contrib import admin

# Register your models here.
from nested_inlines.admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from documents.models import Database, Language, Project, Corpus, Document, Ngram, NgramDocument, List, ListNgram

class DocumentInLine(admin.StackedInline):
    model = Document
    extra = 0

class CorpusInLine(admin.StackedInline):
    model = Corpus
    extra = 0
    inlines = [DocumentInLine,]

class ProjectAdmin(admin.ModelAdmin):
    exclude = ('analyst',)
    list_display = ('title', 'date', 'analyst')
    inlines = [CorpusInLine,]

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(ProjectAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.analyst.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Project.objects.all()
        
        return Project.objects.filter(analyst=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.analyst = request.user
        obj.save()


class CorpusAdmin(admin.ModelAdmin):
    exclude = ('analyst',)
    list_display = ('title', 'date', 'database', 'analyst')
    inlines = [DocumentInLine,]


    def has_change_permission(self, request, obj=None):
        has_class_permission = super(CorpusAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.analyst.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Corpus.objects.all()
        
        return Corpus.objects.filter(analyst=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.analyst = request.user
        obj.save()


class DocumentAdmin(admin.ModelAdmin):
    exclude = ('analyst',)
    list_display = ('date', 'source', 'title')
    list_per_page = 20


    def has_change_permission(self, request, obj=None):
        has_class_permission = super(DocumentAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.analyst.id:
            return False
        return True

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Document.objects.all()
        
        return Document.objects.filter(analyst=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.analyst = request.user
        obj.save()

admin.site.register(Database)
admin.site.register(Language)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Document, DocumentAdmin)


admin.site.register(Ngram)
admin.site.register(NgramDocument)
admin.site.register(List)
admin.site.register(ListNgram)
