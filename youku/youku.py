# -*- coding: utf-8 -*-

# Copyright (c) 2013 Kura
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

from docutils import nodes
from docutils.parsers.rst import directives, Directive


class Youku(Directive):
    """ Embed Youku video in posts.

    VIDEO_ID is required, with / height are optional integer,
    and align could be left / center / right.

    Usage:
    .. youku:: VIDEO_ID
        :align: center
    """

    def align(argument):
        """Conversion function for the "align" option."""
        return directives.choice(argument, ('left', 'center', 'right'))

    required_arguments = 1
    optional_arguments = 2
    option_spec = {
        'align': align
    }

    final_argument_whitespace = False
    has_content = False

    def run(self):
        videoID = self.arguments[0].strip()
        width = 420
        height = 315
        align = 'left'

        if 'width' in self.options:
            width = self.options['width']

        if 'height' in self.options:
            height = self.options['height']

        if 'align' in self.options:
            align = self.options['align']

        div_block = '<div class="embed-responsive embed-responsive-16by9" align="{}">'.format(align)
        embed_block = '<embed src="http://player.youku.com/player.php/sid/{}/v.swf" allowFullScreen="true" quality="high" align="middle" allowScriptAccess="always" type="application/x-shockwave-flash"></embed>'.format(videoID)

        return [
            nodes.raw('', div_block, format='html'),
            nodes.raw('', embed_block, format='html'),
            nodes.raw('', '</div>', format='html')]


def register():
    directives.register_directive('youku', Youku)