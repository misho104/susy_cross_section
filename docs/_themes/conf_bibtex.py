# cSpell:words pybtex unsrt arxiv eprint

from pybtex.plugin import register_plugin
from pybtex.style.formatting import toplevel
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.formatting.unsrt import date, pages
from pybtex.style.template import (  # noqa: F401
    field,
    first_of,
    href,
    join,
    names,
    optional,
    optional_field,
    sentence,
    tag,
    together,
    words,
)


class MyStyle(UnsrtStyle):
    default_sorting_style = "author_year_title"
    default_label_style = "alpha"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.abbreviate_names = True

    def format_title(self, e, which_field, as_sentence=True):
        formatted_title = tag("em")[
            field(which_field, apply_func=lambda text: text.capitalize())
        ]
        if as_sentence:
            return sentence[formatted_title]
        else:
            return formatted_title

    def format_repository(self, e):
        return first_of[
            optional[
                href[join["https://github.com/", field("github", raw=True)], "(GitHub)"]
            ]
        ]

    def get_article_template(self, e):
        arxiv_url = join["https://arxiv.org/abs/", field("eprint", raw=True)]
        doi_url = join["https://doi.org/", field("doi", raw=True)]
        journal_text = join(" ")[
            field("journal"),
            tag("strong")[field("volume")],
            join["(", field("year"), ")"],
            pages,
        ]

        journal = first_of[
            optional[
                join[
                    href[doi_url, journal_text],
                    " [",
                    href[arxiv_url, field("eprint", raw=True)],
                    "]",
                ]
            ],
            optional[
                join[
                    journal_text, " [", href[arxiv_url, field("eprint", raw=True)], "]",
                ]
            ],
            optional[href[doi_url, journal_text]],
            optional[journal_text],
            optional[href[arxiv_url, join["arXiv:", field("eprint", raw=True)]]],
        ]

        template = toplevel[
            self.format_names("author"),
            self.format_title(e, "title"),
            optional[sentence[journal]],
            sentence[optional_field("note")],
            self.format_repository(e),
        ]
        return template

    def get_misc_template(self, e):
        howpublished = first_of[
            # url format
            sentence[
                href[field("url", raw=True), field("url", raw=True)],
                optional[join["Retrieved ", field("retrieved")]],
            ],
            # raw format
            sentence[optional[field("howpublished")], optional[date]],
        ]

        template = toplevel[
            optional[sentence[self.format_names("author")]],
            optional[self.format_title(e, "title")],
            optional[howpublished],
            sentence[optional_field("note")],
        ]
        return template


register_plugin("pybtex.style.formatting", "default", MyStyle)


def setup(app):
    return {"parallel_read_safe": True, "parallel_write_safe": True}
