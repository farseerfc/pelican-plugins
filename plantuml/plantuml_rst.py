#!/usr/bin/env python
"""Custom reST_ directive for plantuml_ integration.
   Adapted from ditaa_rst plugin.

.. _reST: http://docutils.sourceforge.net/rst.html
.. _plantuml: http://plantuml.sourceforge.net/
"""

from __future__ import unicode_literals
import sys
import os
import tempfile
import io

from subprocess import Popen,PIPE
from zlib import adler32

from docutils import utils
from docutils.nodes import paragraph, raw, image, literal_block
from docutils.parsers.rst import Directive, directives
from pelican import signals, logger

from .generateUmlDiagram import generate_uml_image


global_siteurl = "" # URL of the site, filled on plugin initialization


class PlantUML_rst(Directive):
    """ reST directive for PlantUML """
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    global global_siteurl

    option_spec = {
        'class': directives.class_option,
        'alt': directives.unchanged,
        'format': directives.unchanged,
    }

    def run(self):

        path = os.path.abspath(os.path.join('content', 'uml'))

        if not os.path.exists(path):
            os.makedirs(path)

        nodes = []
        body = '\n'.join(self.content)
        tf = tempfile.NamedTemporaryFile(delete=True)
        tf.write('@startuml\n'.encode('utf-8'))
        tf.write(body.encode('utf8'))
        tf.write('\n@enduml'.encode('utf-8'))
        tf.flush()

        imgformat = self.options.get('format', 'png')

        if imgformat == 'png':
            imgext = ".png"
            outopt = "-tpng"
        elif imgformat == 'svg':
            imgext = ".svg"
            outopt = "-tsvg"
        else:
            logger.error("Bad uml image format: " + imgformat)

        # make a name
        name = tf.name + imgext

        alt = self.options.get('alt', 'uml diagram')
        classes = self.options.pop('class', ['uml'])
        cmdline = ['plantuml', '-o', path, outopt, tf.name]

        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
        except Exception as exc:
            error = self.state_machine.reporter.error(
                'Failed to run plantuml: %s' % exc,
                literal_block(self.block_text, self.block_text),
                line=self.lineno)
            nodes.append(error)
        else:
            if p.returncode == 0:
                # renaming output image using an hash code, just to not pullate
                # output directory with a growing number of images
                name = os.path.join(path, os.path.basename(name))
                newname = os.path.join(path,
                    "%08x" % (adler32(body.encode('utf8')) & 0xffffffff))+imgext

                try:  # for Windows
                    os.remove(newname)
                except Exception as exc:
                    logger.debug('File '+newname+' does not exist, not deleted')

                os.rename(name, newname)
                url = global_siteurl + '/uml/' + os.path.basename(newname)
                imgnode = image(uri=url, classes=classes, alt=alt)
                nodes.append(imgnode)
            else:
                error = self.state_machine.reporter.error(
                    'Error in "%s" directive: %s' % (self.name, err),
                    literal_block(self.block_text, self.block_text),
                    line=self.lineno)
                nodes.append(error)
        return nodes


class Tikz(Directive):
    """ reST directive for TikZ """
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    global global_siteurl

    option_spec = {
        'class': directives.class_option,
        'alt': directives.unchanged,
        'format': directives.unchanged,
        'libs': directives.unchanged,
    }

    def run(self):

        path = os.path.abspath(os.path.join('content', 'uml'))

        if not os.path.exists(path):
            os.makedirs(path)

        nodes = []
        body = '\n'.join(self.content)
        if self.options.get('libs', False):
            libs = '\n'.join(('\\usetikzlibrary{%s}' % x) for x in self.options.get('libs', False).split(','))
        else:
            libs = ''
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.write(('\\documentclass{standalone}\n\\usepackage{xeCJK,fontspec,xunicode}\\usepackage{tikz}\setCJKmainfont{Noto Sans CJK TC}\n%s\n\\begin{document}\\begin{tikzpicture}\n' % libs).encode('utf-8'))
        tf.write(body.encode('utf8'))
        tf.write('\n\\end{tikzpicture}\\end{document}'.encode('utf-8'))
        tf.flush()

        imgformat = self.options.get('format', 'svg')
        imgext = ".svg"


        # make a name
        name = tf.name + imgext
        output_path = os.path.join(path, os.path.basename(name))

        alt = self.options.get('alt', 'tikz diagram')
        classes = self.options.pop('class', ['tikz'])
        cmdline = ['tikz2svg', tf.name, output_path]
        logger.debug("running: "+ ' '.join(cmdline))

        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            logger.debug("tikz2svg out: "+ out.decode('utf-8'))
            logger.debug("tikz2svg err: "+ err.decode('utf-8'))
        except Exception as exc:
            error = self.state_machine.reporter.error(
                'Failed to run tikz: %s' % exc,
                literal_block(self.block_text, self.block_text),
                line=self.lineno)
            nodes.append(error)
        else:
            if p.returncode == 0:
                # renaming output image using an hash code, just to not pullate
                # output directory with a growing number of images
                newname = os.path.join(path,
                    "%08x" % (adler32(body.encode('utf8')) & 0xffffffff))+imgext

                try:  # for Windows
                    os.remove(newname)
                except Exception as exc:
                    logger.debug('File '+newname+' does not exist, not deleted')

                os.rename(output_path, newname)
                url = global_siteurl + '/uml/' + os.path.basename(newname)
                imgnode = image(uri=url, classes=classes, alt=alt)
                nodes.append(imgnode)
            else:
                error = self.state_machine.reporter.error(
                    'Error in "%s" directive: %s' % (self.name, err),
                    literal_block(self.block_text, self.block_text),
                    line=self.lineno)
                nodes.append(error)
        return nodes

class Ditaa(Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    global global_siteurl

    option_spec = {
        'class' : directives.class_option,
        'alt'   : directives.unchanged,
        'format': directives.unchanged,
    }

    def run(self):

        path = os.path.abspath(os.path.join('content', 'uml'))

        if not os.path.exists(path):
            os.makedirs(path)

        nodes = []

        body = '\n'.join(self.content)
        tf = tempfile.NamedTemporaryFile(delete=True)
        tf.write(body.encode('utf8'))
        tf.flush()

        imgext = ".png"

        # make a name
        name = tf.name + imgext

        output_path = os.path.join(path, os.path.basename(name))

        alt = self.options.get('alt', 'ditaa diagram')
        classes = self.options.pop('class', ['ditaa'])
        cmdline = ['ditaa', '-v', '-o', tf.name, output_path]

        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
        except Exception as exc:
            error = self.state_machine.reporter.error(
                'Failed to run ditaa: %s' % (exc, ),
                literal_block(self.block_text, self.block_text),
                line=self.lineno)
            nodes.append(error)
        else:
            if p.returncode == 0:
                # renaming output image using an hash code, just to not pullate
                # output directory with a growing number of images
                name = os.path.join(path, os.path.basename(name))
                newname = os.path.join(path, "%08x" % (adler32(body.encode('utf8')) & 0xffffffff))+imgext

                try:  # for Windows
                    os.remove(newname)
                except Exception as exc:
                    logger.debug('File '+newname+' does not exist, not deleted')

                os.rename(name, newname)
                url = global_siteurl + '/uml/' + os.path.basename(newname)
                imgnode = image(uri=url, classes=classes, alt=alt)
                nodes.append(imgnode)
            else:
                error = self.state_machine.reporter.error(
                    'Error in "%s" directive: %s' % (self.name, err),
                    literal_block(self.block_text, self.block_text),
                    line=self.lineno)
                nodes.append(error)

        return nodes

def make_graphviz(layout):
    class Graphviz(Directive):
        required_arguments = 0
        optional_arguments = 0
        has_content = True

        global global_siteurl

        option_spec = {
            'class' : directives.class_option,
            'alt'   : directives.unchanged,
            'format': directives.unchanged,
        }

        def run(self):
            nodes = []

            body = '\n'.join(self.content)

            alt = self.options.get('alt', 'Graphviz diagram')
            classes = self.options.pop('class', ['graphviz'])
            cmdline = [layout, '-Tsvg']

            try:
                p = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                out, err = p.communicate(input=body.encode('utf8'))
            except Exception as exc:
                error = self.state_machine.reporter.error(
                    'Failed to run %s: %s' % (layout, exc),
                    literal_block(self.block_text, self.block_text),
                    line=self.lineno)
                nodes.append(error)
            else:
                if p.returncode == 0:
                    svg = out.decode('utf-8')
                    imgnode = raw(svg, svg, format="html")
                    nodes.append(imgnode)
                else:
                    error = self.state_machine.reporter.error(
                        'Error in "%s" directive: %s' % (self.name, err),
                        literal_block(self.block_text, self.block_text),
                        line=self.lineno)
                    nodes.append(error)

            return nodes
    return Graphviz

def custom_url(generator, metadata):
    """ Saves globally the value of SITEURL configuration parameter """
    global global_siteurl
    global_siteurl = generator.settings['SITEURL']
    if "/" in global_siteurl[2:]:  # trim "//" from url, and return to origin SITEURL for subsites
        global_siteurl = global_siteurl[:global_siteurl.rindex("/")]


def pelican_init(pelicanobj):
    """ Prepare configurations for the MD plugin """
    try:
        import markdown
        from plantuml_md import PlantUMLMarkdownExtension
    except:
        # Markdown not available
        logger.debug("[plantuml] Markdown support not available")
        return

    # Register the Markdown plugin
    config = { 'siteurl': pelicanobj.settings['SITEURL'] }

    try:
        pelicanobj.settings['MD_EXTENSIONS'].append(PlantUMLMarkdownExtension(config))
    except:
        logger.error("[plantuml] Unable to configure plantuml markdown extension")


def register():
    """Plugin registration."""
    signals.initialized.connect(pelican_init)
    signals.article_generator_context.connect(custom_url)
    directives.register_directive('ditaa', Ditaa)
    directives.register_directive('uml', PlantUML_rst)
    directives.register_directive('tikz', Tikz)
    graphviz_filters = 'dot neato twopi circo fdp sfdp patchwork osage'.split(' ')
    for f in graphviz_filters:
        directives.register_directive(f, make_graphviz(f))
