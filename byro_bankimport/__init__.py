from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class PluginApp(AppConfig):
    name = 'byro_bankimport'
    verbose_name = 'Byro Bank CSV Import'

    class ByroPluginMeta:
        name = ugettext_lazy('Byro Bank CSV Import')
        author = 'Annika Hannig'
        description = ugettext_lazy('Short description')
        visible = True
        version = '0.0.1'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'byro_bankimport.PluginApp'
