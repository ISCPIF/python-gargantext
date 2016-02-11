from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *

from datetime import datetime


@requires_auth
def overview(request):
    '''This view show all projects for a given user.
    Each project is described with hyperdata that are updateded on each following view.
    To each project, we can link a resource that can be an image.
    '''

    user = cache.User[request.user.username]
    project_type = cache.NodeType['Project']

    # If POST method, creates a new project...
    if request.method == 'POST':
        name = str(request.POST['name'])
        if name != '':
            new_project = Node(
                name = name,
                type_id = project_type.id,
                user_id = user.id,
            )
            session.add(new_project)
            session.commit()

    # list of projects created by the logged user
    user_projects = user.get_nodes(nodetype=project_type)

    # list of contacts of the logged user
    contacts = user.get_contacts()
    contacts_projects = []
    for contact in contacts:
        contact_projects = (session
            .query(Node)
            .filter(Node.user_id == contact.id)
            .filter(Node.type_id == project_type.id)
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


@requires_auth
def project(request, project_id):
    return render(
        template_name = 'pages/projects/project.html',
        request = request,
        context = {
            # 'debug': settings.DEBUG,
            # 'date': datetime.now(),
            # # projects owned by the user
            # 'number': len(user_projects),
            # 'projects': user_projects,
            # # projects owned by the user's contacts
            # 'common_users': contacts if len(contacts) else False,
            # 'common_projects': contacts_projects if len(contacts_projects) else False,
        },
    )
