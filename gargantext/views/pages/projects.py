from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *

from datetime import datetime


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
                type = 'PROJECT',
                name = name,
            )
            session.add(new_project)
            session.commit()

    # list of projects created by the logged user
    user_projects = user.get_nodes(type='PROJECT')

    # list of contacts of the logged user
    contacts = user.get_contacts()
    contacts_projects = []
    for contact in contacts:
        contact_projects = (session
            .query(Node)
            .filter(Node.user_id == contact.id)
            .filter(Node.type == 'PROJECT')
            .order_by(Node.date)
        ).all()
        contacts_projects += contact_projects

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
            'common_users': contacts if len(contacts) else False,
            'common_projects': contacts_projects if len(contacts_projects) else False,
        },
    )


from django.utils.translation import ugettext_lazy
class NewCorpusForm(forms.Form):
    type = forms.ChoiceField(
        choices = enumerate(resourcetype['name'] for resourcetype in RESOURCETYPES),
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
    project = session.query(Node).filter(project_id == project_id).first()
    return render(
        template_name = 'pages/projects/project.html',
        request = request,
        context = {
            'form': NewCorpusForm,
            'user': request.user,
            'date': datetime.now(),
            'project': project,
            'donut': donut,
            # 'list_corpora'  : dict(corpora_by_resourcetype),
            'whitelists': [],
            'blacklists': [],
            'cooclists': [],
            # 'number'        : corpora_count,
            # 'query_size'    : QUERY_SIZE_N_DEFAULT,
        },
    )
