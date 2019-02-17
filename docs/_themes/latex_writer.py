# cSpell:words docutils

import docutils.nodes
import sphinx.writers.latex


class MyTranslator(sphinx.writers.latex.LaTeXTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def visit_citation_reference(self, node):
        origref = str(node.children[0])[1:-1]
        if self.in_title:
            pass
        else:
            self.body.append('\\cite{%s}' % (origref))
            raise docutils.nodes.SkipNode


def setup(app):
    app.set_translator('latex', MyTranslator)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
