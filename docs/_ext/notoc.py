from docutils.parsers.rst import Directive
from docutils import nodes


class NoTocDirective(Directive):
    has_content = False

    def run(self):
        # Create a raw HTML node to add the no-right-toc class to body
        html = '<script>document.body.classList.add("no-right-toc");</script>'
        return [nodes.raw("", html, format="html")]


def setup(app):
    app.add_directive("notoc", NoTocDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
