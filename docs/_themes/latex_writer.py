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
            self.body.append("\\cite{%s}" % (origref))
            raise docutils.nodes.SkipNode

    def visit_field_list(self, node):
        self.body.append("\\begin{description}\n")
        if self.table:
            self.table.has_problematic = True

    def depart_field_list(self, node):
        self.body.append("\\end{description}\n")

    def visit_field_name(self, node):
        self.in_term += 1
        ctx = ""
        if node.get("ids"):
            ctx = "\\phantomsection"
            for node_id in node["ids"]:
                ctx += self.hypertarget(node_id, anchor=False)
        ctx += "}] \\leavevmode"
        self.body.append("\\item[\\mdseries\\sffamily{")
        self.context.append(ctx)

    def visit_emphasis(self, node):
        if node.get("refclass") == "type":
            self.body.append(r"\emphasisfortype{")
        else:
            return super().visit_emphasis(node)

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.body.append(", ")
        else:
            self.first_param = 0
        if not node.hasattr("noemph"):
            self.body.append(r"\paramemph{")


def setup(app):
    app.set_translator("latex", MyTranslator)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
