from gargantext.util import workflow
from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *

from datetime import datetime
from collections import defaultdict
import re


@requires_auth
def overview(request):
    '''This view show all projects for a given user.
    Each project is described with hyperdata that are updateded on each following view.
    To each project, we can link a resource that can be an image.
    '''

    user = cache.User[request.user.username]

    # If POST method, creates a new project...
    if request.method == 'POST':
        name = str(request.POST['name'])
        if name != '':
            new_project = Node(
                user_id = user.id,
                typename = 'PROJECT',
                name = name,
            )
            session.add(new_project)
            session.commit()

    # list of projects created by the logged user
    user_projects = user.nodes(typename='PROJECT')

    # list of contacts of the logged user
    contacts_projects = list(user.contacts_nodes(typename='PROJECT'))

    # render page
    return render(
        template_name = 'pages/projects/overview.html',
        request = request,
        context = {
            'debug': settings.DEBUG,
            'date': datetime.now(),
            # projects owned by the user
            'number': len(user_projects),
            'projects': user_projects,
            # projects owned by the user's contacts
            'common_users': (contact for contact, projects in contacts_projects),
            'common_projects': sum((projects for contact, projects in contacts_projects), []),
        },
    )


from django.utils.translation import ugettext_lazy
class NewCorpusForm(forms.Form):
    type = forms.ChoiceField(
        choices = enumerate(resource_type['name'] for resource_type in RESOURCETYPES),
        widget = forms.Select(attrs={'onchange':'CustomForSelect( $("option:selected", this).text() );'})
    )
    name = forms.CharField( label='Name', max_length=199 , widget=forms.TextInput(attrs={ 'required': 'true' }))
    file = forms.FileField()
    def clean_file(self):
        file_ = self.cleaned_data.get('file')
        if len(file_) > 1024 ** 3: # we don't accept more than 1GB
            raise forms.ValidationError(ugettext_lazy('File too heavy! (>1GB).'))
        return file_

@requires_auth
def project(request, project_id):
    # current user
    user = cache.User[request.user.username]
    # viewed project
    project = session.query(Node).filter(Node.id == project_id).first()
    if project is None:
        raise Http404()
    if not user.owns(project):
        raise HttpResponseForbidden()

    # new corpus
    if request.method == 'POST':
        corpus = project.add_corpus(
            name = request.POST['name'],
            resource_type = request.POST['type'],
            resource_upload = request.FILES['file'],
        )
        workflow.parse(corpus.id)

    # corpora within this project
    corpora = project.children('CORPUS').all()
    corpora_by_source = defaultdict(list)
    for corpus in corpora:
        resource_type = RESOURCETYPES[corpus['resource_type']]
        corpora_by_source[resource_type['name']].append(corpus)
    # source & their respective counts
    total_count = 0
    sources_counts = defaultdict(int)
    for document in corpora:
        source = RESOURCETYPES[document['resource_type']]
        sourcename = re.sub(' \(.*$', '', source['name'])
        count = document.children('DOCUMENT').count()
        sources_counts[sourcename] += count
        count += total_count
    donut = [
        {   'source': sourcename,
            'count': count,
            'part' : round(count * 100.0 / total_count) if total_count else 0,
        }
        for sourcename, count in sources_counts.items()
    ]
    # response!
    return render(
        template_name = 'pages/projects/project.html',
        request = request,
        context = {
            'form': NewCorpusForm,
            'user': request.user,
            'date': datetime.now(),
            'project': project,
            'donut': donut,
            'list_corpora': dict(corpora_by_source),
            'whitelists': [],
            'blacklists': [],
            'cooclists': [],
            'number': len(corpora),
            'query_size': QUERY_SIZE_N_DEFAULT,
        },
    )
