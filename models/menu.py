# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = A(B('web',SPAN(2),'py'),XML('&trade;&nbsp;'),
                  _class="brand",_href="http://www.web2py.com/")
response.title = request.application.replace('_',' ').title()
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Cliff'
response.meta.description = 'Listen to music with the help from LastFm'
response.meta.keywords = 'web2py, python, jPlayer, LastFM'
response.meta.generator = 'LastFM Media Player'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Home'), False, URL('default', 'index'), []),
	(T('Files'), False, URL('default', 'files'), [])
]

DEVELOPMENT_MENU = False
if "auth" in locals(): auth.wikimenu() 
