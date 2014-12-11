"""
Summary
-------

This plugin allows easy, variable length summaries directly embedded into the
body of your articles.
"""

from __future__ import unicode_literals
from pelican import signals
from pelican.generators import ArticlesGenerator, StaticGenerator, PagesGenerator

def initialized(pelican):
    from pelican.settings import DEFAULT_CONFIG
    DEFAULT_CONFIG.setdefault('SUMMARY_BEGIN_MARKER',
                              '<!-- PELICAN_BEGIN_SUMMARY -->')
    DEFAULT_CONFIG.setdefault('SUMMARY_END_MARKER',
                              '<!-- PELICAN_END_SUMMARY -->')
    if pelican:
        pelican.settings.setdefault('SUMMARY_BEGIN_MARKER',
                                    '<!-- PELICAN_BEGIN_SUMMARY -->')
        pelican.settings.setdefault('SUMMARY_END_MARKER',
                                    '<!-- PELICAN_END_SUMMARY -->')

def extract_summary(instance):
    # if summary is already specified, use it
    # if there is no content, there's nothing to do
    if hasattr(instance, '_summary'):
        instance.has_summary = True
        return

    if not instance._content:
        instance.has_summary = False
        return

    begin_marker = instance.settings['SUMMARY_BEGIN_MARKER']
    end_marker   = instance.settings['SUMMARY_END_MARKER']

    content = instance._content
    begin_summary = -1
    end_summary = -1
    if begin_marker:
        begin_summary = content.find(begin_marker)
    if end_marker:
        end_summary = content.find(end_marker)

    if begin_summary == -1 and end_summary == -1:
        instance.has_summary = False
        return

    # skip over the begin marker, if present
    if begin_summary == -1:
        begin_summary = 0
    else:
        begin_summary = begin_summary + len(begin_marker)

    if end_summary == -1:
        end_summary = None

    summary = content[begin_summary:end_summary]

    # remove the markers from the content
    if begin_summary:
        content = content.replace(begin_marker, '', 1)
    if end_summary:
        content = content.replace(end_marker, '', 1)

    instance._content = content
    instance._summary = summary
    instance.has_summary = True


def run_plugin(generators):
    for generator in generators:
        if isinstance(generator, ArticlesGenerator):
            for article in generator.articles:
                extract_summary(article)
        elif isinstance(generator, PagesGenerator):
            for page in generator.pages:
                extract_summary(page)

    def _get_content(self):
        content = self._content
        if self.settings['SUMMARY_BEGIN_MARKER']:
            content = content.replace(
                self.settings['SUMMARY_BEGIN_MARKER'], '', 1)
        if self.settings['SUMMARY_END_MARKER']:
            content = content.replace(
                self.settings['SUMMARY_END_MARKER'], '', 1)
        return content
    instance._get_content = types.MethodType(_get_content, instance)

    # extract out our summary
    if not hasattr(instance, '_summary') and instance._content is not None:
        content = instance._content
        begin_summary = -1
        end_summary = -1
        last_end = 0
        summary = None
        while last_end != -1 and last_end < len(content):
            if instance.settings['SUMMARY_BEGIN_MARKER']:
                begin_summary = content.find(instance.settings['SUMMARY_BEGIN_MARKER'], last_end)
            if instance.settings['SUMMARY_END_MARKER']:
                end_summary = content.find(instance.settings['SUMMARY_END_MARKER'], last_end)
            if end_summary == -1:
                last_end = -1
            else:
                last_end = end_summary + len(instance.settings['SUMMARY_END_MARKER'])
            if summary is None:  # first time
                if begin_summary != -1 or end_summary != -1:
                    # the beginning position has to take into account the length
                    # of the marker
                    begin_summary = (begin_summary +
                                    len(instance.settings['SUMMARY_BEGIN_MARKER'])
                                    if begin_summary != -1 else 0)
                    end_summary = end_summary if end_summary != -1 else None
                    summary = instance._update_content(content[begin_summary:end_summary], instance._context.get('localsiteurl', ''))
            else:
                if begin_summary == -1 or end_summary == -1:
                    break
                begin_summary = (begin_summary +
                                len(instance.settings['SUMMARY_BEGIN_MARKER'])
                                if begin_summary != -1 else 0)
                end_summary = end_summary if end_summary != -1 else None
                summary += instance._update_content(content[begin_summary:end_summary], instance._context.get('localsiteurl', ''))
        if summary is not None:
            instance._summary = summary

def register():
    signals.initialized.connect(initialized)
    try:
        signals.all_generators_finalized.connect(run_plugin)
    except AttributeError:
        # NOTE: This results in #314 so shouldn't really be relied on
        # https://github.com/getpelican/pelican-plugins/issues/314
        signals.content_object_init.connect(extract_summary)
