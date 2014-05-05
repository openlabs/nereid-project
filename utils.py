# -*- coding: utf-8 -*-
"""
    utils

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import warnings

from trytond.pool import Pool
from trytond.config import CONFIG
from trytond.tools import get_smtp_server
from nereid import request, render_email
from nereid.signals import registration


def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


@registration.connect
def invitation_new_user_handler(nereid_user_id):
    """When the invite is sent to a new user, he is sent an invitation key
    with the url which guides the user to registration page

        This method checks if the invitation key is present in the url
        If yes, search for the invitation with this key, attache the user
            to the invitation and project to the user
        If not, perform normal operation
    """
    try:
        Invitation = Pool().get('project.work.invitation')
        Project = Pool().get('project.work')
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')

    except KeyError:
        # Just return silently. This KeyError is cause if the module is not
        # installed for a specific database but exists in the python path
        # and is loaded by the tryton module loader
        warnings.warn(
            "nereid-project module installed but not in database",
            DeprecationWarning, stacklevel=2
        )
        return

    invitation_code = request.args.get('invitation_code')
    if not invitation_code:
        return
    invitation, = Invitation.search([
        ('invitation_code', '=', invitation_code)
    ], limit=1)

    if not invitation:
        return

    Invitation.write([invitation], {
        'nereid_user': nereid_user_id,
        'invitation_code': None
    })

    nereid_user = NereidUser(nereid_user_id)

    subject = '[%s] %s Accepted the invitation to join the project' \
        % (invitation.project.rec_name, nereid_user.display_name)

    receivers = [
        p.email for p in invitation.project.company.project_admins if p.email
    ]

    email_message = render_email(
        text_template='project/emails/invite_2_project_accepted_text.html',
        subject=subject, to=', '.join(receivers),
        from_email=CONFIG['smtp_from'], invitation=invitation
    )
    server = get_smtp_server()
    server.sendmail(CONFIG['smtp_from'], receivers, email_message.as_string())
    server.quit()

    Project.write(
        [invitation.project], {
            'participants': [('add', [nereid_user_id])]
        }
    )
    Activity.create([{
        'actor': nereid_user_id,
        'object_': 'project.work, %d' % invitation.project.id,
        'verb': 'joined_project',
        'project': invitation.project.id,
    }])
